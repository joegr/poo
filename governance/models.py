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
            ('start_discussion', 'Can start discussion phase'),
            ('start_voting', 'Can start voting phase'),
            ('execute_proposal', 'Can execute proposal'),
            ('cancel_proposal', 'Can cancel proposal'),
        ]
    
    def __str__(self):
        """Return a string representation of the proposal."""
        return f"{self.title} ({self.get_status_display()})"
    
    def start_discussion(self):
        """Start the discussion phase for this proposal."""
        self.status = self.Status.DISCUSSION
        self.discussion_start_time = timezone.now()
        self.save()
    
    def start_voting(self):
        """Start the voting phase for this proposal."""
        self.status = self.Status.VOTING
        self.voting_start_time = timezone.now()
        
        # Set voting end time based on settings
        voting_period = timezone.timedelta(days=settings.PROPOSAL_VOTING_PERIOD_DAYS)
        self.voting_end_time = self.voting_start_time + voting_period
        
        self.save()
    
    def end_voting(self):
        """End the voting phase and determine if the proposal passed."""
        # Calculate if the proposal passed
        quorum_percentage = settings.PROPOSAL_QUORUM_PERCENTAGE
        approval_threshold = settings.PROPOSAL_APPROVAL_THRESHOLD
        
        total_votes = self.total_votes_for + self.total_votes_against
        
        # Check if quorum was reached
        if total_votes < (self.total_voting_power * quorum_percentage / 100):
            self.status = self.Status.REJECTED
            self.save()
            return False
        
        # Check if approval threshold was met
        if total_votes > 0 and (self.total_votes_for / total_votes * 100) >= approval_threshold:
            self.status = self.Status.APPROVED
            self.save()
            return True
        else:
            self.status = self.Status.REJECTED
            self.save()
            return False
    
    def execute(self):
        """Execute the approved proposal."""
        self.status = self.Status.EXECUTED
        self.execution_time = timezone.now()
        self.save()
    
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
        """Return a string representation of the vote."""
        direction = "FOR" if self.is_for else "AGAINST"
        return f"{self.voter.username} voted {direction} with {self.vote_count} votes"
    
    @staticmethod
    def calculate_vote_cost(vote_count):
        """Calculate the cost of votes using quadratic voting."""
        return vote_count ** 2
    
    def save(self, *args, **kwargs):
        """Override save to calculate vote cost and update proposal totals."""
        # Calculate vote cost
        self.vote_cost = self.calculate_vote_cost(self.vote_count)
        
        # Save the vote
        super().save(*args, **kwargs)
        
        # Update proposal vote totals
        proposal = self.proposal
        votes = Vote.objects.filter(proposal=proposal)
        
        proposal.total_votes_for = sum(v.vote_count for v in votes if v.is_for)
        proposal.total_votes_against = sum(v.vote_count for v in votes if not v.is_for)
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
        """Return a string representation of the comment."""
        return f"Comment by {self.author.username} on {self.proposal.title}"


class GovernanceToken(models.Model):
    """Model for governance tokens."""
    
    holder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='governance_tokens')
    balance = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    delegated_to = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='delegated_tokens'
    )
    is_locked = models.BooleanField(default=False)
    
    class Meta:
        """Meta options for the GovernanceToken model."""
        
        constraints = [
            models.UniqueConstraint(
                fields=['holder'],
                name='unique_token_holder'
            )
        ]
    
    def __str__(self):
        """Return a string representation of the token."""
        return f"{self.holder.username}'s tokens: {self.balance}"
    
    def lock_for_voting(self, days=30):
        """Lock tokens for a specified number of days."""
        self.locked_until = timezone.now() + timezone.timedelta(days=days)
        self.is_locked = True
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
    term_start_date = models.DateField()
    term_end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        """Meta options for the Guardian model."""
        
        permissions = [
            ('approve_transaction', 'Can approve treasury transactions'),
            ('reject_transaction', 'Can reject treasury transactions'),
        ]
    
    def __str__(self):
        """Return a string representation of the guardian."""
        return f"Guardian: {self.user.username}"


class Member(models.Model):
    """Model for DAO members."""
    
    class VerificationStatus(models.TextChoices):
        """Verification status choices."""
        
        UNVERIFIED = 'UNVERIFIED', 'Unverified'
        PENDING = 'PENDING', 'Pending Verification'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Verification Rejected'
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member')
    wallet_address = models.CharField(max_length=255, unique=True)
    verification_status = models.CharField(
        max_length=20, 
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNVERIFIED
    )
    join_date = models.DateField(auto_now_add=True)
    reputation_score = models.PositiveIntegerField(default=0)
    
    class Meta:
        """Meta options for the Member model."""
        
        permissions = [
            ('verify_member', 'Can verify member identity'),
            ('reject_member', 'Can reject member verification'),
        ]
    
    def __str__(self):
        """Return a string representation of the member."""
        return f"Member: {self.user.username} ({self.get_verification_status_display()})"


class VerificationRequest(models.Model):
    """Model for member verification requests."""
    
    class Status(models.TextChoices):
        """Status choices for verification requests."""
        
        PENDING_REVIEW = 'PENDING', 'Pending Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        ADDITIONAL_INFO = 'ADDITIONAL_INFO', 'Additional Information Requested'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_requests')
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField()
    country = models.CharField(max_length=100)
    id_document_type = models.CharField(max_length=100)
    id_document_number = models.CharField(max_length=100)
    document_front_image = models.TextField()  # Base64 encoded image
    document_back_image = models.TextField()  # Base64 encoded image
    selfie_image = models.TextField()  # Base64 encoded image
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_REVIEW)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for the VerificationRequest model."""
        
        ordering = ['-created_at']
    
    def __str__(self):
        """Return a string representation of the verification request."""
        return f"Verification request for {self.user.username} ({self.get_status_display()})"


class CircuitBreaker(models.Model):
    """Model for governance circuit breaker."""
    
    is_active = models.BooleanField(default=False)
    activation_time = models.DateTimeField(auto_now_add=True)
    deactivation_time = models.DateTimeField(null=True, blank=True)
    reason = models.TextField()
    activated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='activated_circuit_breakers'
    )
    deactivated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deactivated_circuit_breakers'
    )
    
    class Meta:
        """Meta options for the CircuitBreaker model."""
        
        ordering = ['-activation_time']
        permissions = [
            ('activate_circuit_breaker', 'Can activate circuit breaker'),
            ('deactivate_circuit_breaker', 'Can deactivate circuit breaker'),
        ]
    
    def __str__(self):
        """Return a string representation of the circuit breaker."""
        status = "Active" if self.is_active else "Inactive"
        return f"Circuit Breaker: {status} - {self.reason}"
    
    def deactivate(self, user):
        """Deactivate the circuit breaker."""
        self.is_active = False
        self.deactivation_time = timezone.now()
        self.deactivated_by = user
        self.save() 