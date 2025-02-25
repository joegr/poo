"""
Models for the governance app.
"""

import math
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User


class Proposal(models.Model):
    """Model for governance proposals."""
    
    class Status(models.TextChoices):
        """Status choices for proposals."""
        
        DRAFT = 'DRAFT', 'Draft'
        DISCUSSION = 'DISCUSSION', 'In Discussion'
        VOTING = 'VOTING', 'Voting Active'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        QUEUED = 'QUEUED', 'Queued for Execution'
        EXECUTED = 'EXECUTED', 'Executed'
        CANCELLED = 'CANCELLED', 'Cancelled'
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    rationale = models.TextField()
    implementation_details = models.TextField()
    timeline = models.TextField()
    
    # Metadata
    proposer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposals')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Timestamps for each phase
    discussion_start_time = models.DateTimeField(null=True, blank=True)
    voting_start_time = models.DateTimeField(null=True, blank=True)
    voting_end_time = models.DateTimeField(null=True, blank=True)
    execution_time = models.DateTimeField(null=True, blank=True)
    
    # MongoDB document ID for additional content
    content_document_id = models.CharField(max_length=255, null=True, blank=True)
    
    # Voting results
    total_votes_for = models.PositiveIntegerField(default=0)
    total_votes_against = models.PositiveIntegerField(default=0)
    total_voting_power = models.PositiveIntegerField(default=0)
    
    class Meta:
        """Meta options for the Proposal model."""
        
        ordering = ['-created_at']
        permissions = [
            ('can_create_proposal', 'Can create a proposal'),
            ('can_vote_on_proposal', 'Can vote on a proposal'),
            ('can_execute_proposal', 'Can execute a proposal'),
        ]
    
    def __str__(self):
        """String representation of the proposal."""
        return self.title
    
    def start_discussion(self):
        """Start the discussion phase for this proposal."""
        self.status = self.Status.DISCUSSION
        self.discussion_start_time = timezone.now()
        self.save()
    
    def start_voting(self):
        """Start the voting phase for this proposal."""
        self.status = self.Status.VOTING
        self.voting_start_time = timezone.now()
        self.voting_end_time = self.voting_start_time + timezone.timedelta(
            days=settings.PROPOSAL_VOTING_PERIOD_DAYS
        )
        self.save()
    
    def end_voting(self):
        """End the voting phase and determine the outcome."""
        # Calculate quorum
        quorum_reached = (self.total_votes_for + self.total_votes_against) >= (
            self.total_voting_power * settings.PROPOSAL_QUORUM_PERCENTAGE / 100
        )
        
        # Calculate approval
        if self.total_votes_for + self.total_votes_against > 0:
            approval_percentage = (
                self.total_votes_for / (self.total_votes_for + self.total_votes_against)
            ) * 100
        else:
            approval_percentage = 0
        
        # Determine outcome
        if quorum_reached and approval_percentage >= settings.PROPOSAL_APPROVAL_THRESHOLD:
            self.status = self.Status.APPROVED
            # Queue for execution after timelock
            self.execution_time = timezone.now() + timezone.timedelta(
                hours=settings.PROPOSAL_TIMELOCK_HOURS
            )
        else:
            self.status = self.Status.REJECTED
        
        self.save()
    
    def execute(self):
        """Execute the approved proposal."""
        if self.status == self.Status.APPROVED:
            self.status = self.Status.EXECUTED
            self.save()
            # Implementation would trigger the actual execution logic
    
    def cancel(self):
        """Cancel the proposal."""
        self.status = self.Status.CANCELLED
        self.save()


class Vote(models.Model):
    """Model for votes on proposals."""
    
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='votes')
    voter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='votes')
    vote_count = models.PositiveIntegerField(default=0)
    vote_cost = models.PositiveIntegerField(default=0)
    is_for = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        """Meta options for the Vote model."""
        
        unique_together = ('proposal', 'voter')
        ordering = ['-created_at']
    
    def __str__(self):
        """String representation of the vote."""
        direction = "FOR" if self.is_for else "AGAINST"
        return f"{self.voter.username} voted {direction} with {self.vote_count} votes"
    
    @staticmethod
    def calculate_vote_cost(vote_count):
        """Calculate the quadratic cost of votes."""
        return vote_count ** 2
    
    def save(self, *args, **kwargs):
        """Override save to calculate vote cost."""
        self.vote_cost = self.calculate_vote_cost(self.vote_count)
        super().save(*args, **kwargs)
        
        # Update proposal vote counts
        proposal = self.proposal
        proposal_votes = Vote.objects.filter(proposal=proposal)
        
        votes_for = sum(v.vote_count for v in proposal_votes if v.is_for)
        votes_against = sum(v.vote_count for v in proposal_votes if not v.is_for)
        
        proposal.total_votes_for = votes_for
        proposal.total_votes_against = votes_against
        proposal.save(update_fields=['total_votes_for', 'total_votes_against'])


class ProposalComment(models.Model):
    """Model for comments on proposals."""
    
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposal_comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for the ProposalComment model."""
        
        ordering = ['created_at']
    
    def __str__(self):
        """String representation of the comment."""
        return f"Comment by {self.author.username} on {self.proposal.title}"


class GovernanceToken(models.Model):
    """Model for governance tokens."""
    
    holder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='governance_tokens')
    balance = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    delegated_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='delegated_tokens'
    )
    
    class Meta:
        """Meta options for the GovernanceToken model."""
        
        constraints = [
            models.CheckConstraint(
                check=models.Q(balance__gte=0),
                name='governance_token_balance_non_negative'
            )
        ]
    
    def __str__(self):
        """String representation of the governance token."""
        return f"{self.holder.username} - {self.balance} tokens"
    
    def lock_for_voting(self, days=30):
        """Lock tokens after voting to ensure long-term alignment."""
        self.locked_until = timezone.now() + timezone.timedelta(days=days)
        self.save()
    
    def delegate(self, delegate_user):
        """Delegate voting power to another user."""
        self.delegated_to = delegate_user
        self.save()
    
    def undelegate(self):
        """Remove delegation."""
        self.delegated_to = None
        self.save()


class Guardian(models.Model):
    """Model for treasury guardians."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='guardian')
    term_start = models.DateTimeField(auto_now_add=True)
    term_end = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        """Meta options for the Guardian model."""
        
        permissions = [
            ('can_approve_treasury_transactions', 'Can approve treasury transactions'),
        ]
    
    def __str__(self):
        """String representation of the guardian."""
        return f"Guardian: {self.user.username}" 