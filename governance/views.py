"""
Views for the governance app.
"""

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings

from .models import Proposal, Vote, ProposalComment, GovernanceToken, Guardian
from .serializers import (
    ProposalSerializer, VoteSerializer, ProposalCommentSerializer,
    GovernanceTokenSerializer, GuardianSerializer
)


class IsProposalOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of a proposal to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.proposer == request.user


class ProposalViewSet(viewsets.ModelViewSet):
    """
    API endpoint for proposals.
    """
    
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated, IsProposalOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'proposer']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'voting_start_time', 'voting_end_time']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """Create a new proposal."""
        # Check if user has enough tokens to create a proposal
        user = self.request.user
        token = GovernanceToken.objects.filter(holder=user).first()
        
        if not token:
            return Response(
                {"detail": "You don't have any governance tokens."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate total voting power
        total_voting_power = GovernanceToken.objects.aggregate(
            total=Sum('balance')
        )['total'] or 0
        
        # Check if user has at least 1% of total tokens
        required_tokens = total_voting_power * 0.01
        if token.balance < required_tokens:
            return Response(
                {
                    "detail": f"You need at least {required_tokens} tokens to create a proposal. "
                              f"You have {token.balance} tokens."
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save(
            proposer=user,
            status=Proposal.Status.DRAFT,
            total_voting_power=total_voting_power
        )
    
    @action(detail=True, methods=['post'])
    def start_discussion(self, request, pk=None):
        """Start the discussion phase for a proposal."""
        proposal = self.get_object()
        
        if proposal.status != Proposal.Status.DRAFT:
            return Response(
                {"detail": "This proposal is not in draft status."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if proposal.proposer != request.user:
            return Response(
                {"detail": "Only the proposer can start the discussion phase."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        proposal.start_discussion()
        return Response({"status": "discussion started"})
    
    @action(detail=True, methods=['post'])
    def start_voting(self, request, pk=None):
        """Start the voting phase for a proposal."""
        proposal = self.get_object()
        
        if proposal.status != Proposal.Status.DISCUSSION:
            return Response(
                {"detail": "This proposal is not in discussion status."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if discussion period has passed
        if proposal.discussion_start_time:
            discussion_end = proposal.discussion_start_time + timezone.timedelta(
                days=settings.PROPOSAL_DISCUSSION_PERIOD_DAYS
            )
            if timezone.now() < discussion_end:
                return Response(
                    {"detail": "Discussion period has not ended yet."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        proposal.start_voting()
        return Response({"status": "voting started"})
    
    @action(detail=True, methods=['post'])
    def end_voting(self, request, pk=None):
        """End the voting phase for a proposal."""
        proposal = self.get_object()
        
        if proposal.status != Proposal.Status.VOTING:
            return Response(
                {"detail": "This proposal is not in voting status."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if voting period has passed
        if proposal.voting_end_time and timezone.now() < proposal.voting_end_time:
            return Response(
                {"detail": "Voting period has not ended yet."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proposal.end_voting()
        return Response({"status": "voting ended", "result": proposal.status})
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute an approved proposal."""
        proposal = self.get_object()
        
        if proposal.status != Proposal.Status.APPROVED:
            return Response(
                {"detail": "This proposal is not approved."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if timelock period has passed
        if proposal.execution_time and timezone.now() < proposal.execution_time:
            return Response(
                {"detail": "Timelock period has not ended yet."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proposal.execute()
        return Response({"status": "proposal executed"})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a proposal."""
        proposal = self.get_object()
        
        # Only the proposer can cancel a draft or discussion proposal
        if proposal.status in [Proposal.Status.DRAFT, Proposal.Status.DISCUSSION]:
            if proposal.proposer != request.user:
                return Response(
                    {"detail": "Only the proposer can cancel this proposal."},
                    status=status.HTTP_403_FORBIDDEN
                )
        # For approved proposals in timelock, need emergency cancellation vote
        elif proposal.status == Proposal.Status.APPROVED:
            # Implementation for emergency cancellation would go here
            pass
        else:
            return Response(
                {"detail": "This proposal cannot be cancelled in its current state."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proposal.cancel()
        return Response({"status": "proposal cancelled"})


class VoteViewSet(viewsets.ModelViewSet):
    """
    API endpoint for votes.
    """
    
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['proposal', 'voter', 'is_for']
    
    def perform_create(self, serializer):
        """Create a new vote."""
        serializer.save(voter=self.request.user)


class ProposalCommentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for proposal comments.
    """
    
    queryset = ProposalComment.objects.all()
    serializer_class = ProposalCommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['proposal', 'author']
    ordering_fields = ['created_at']
    ordering = ['created_at']
    
    def perform_create(self, serializer):
        """Create a new comment."""
        serializer.save(author=self.request.user)


class GovernanceTokenViewSet(viewsets.ModelViewSet):
    """
    API endpoint for governance tokens.
    """
    
    queryset = GovernanceToken.objects.all()
    serializer_class = GovernanceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['holder']
    
    def get_queryset(self):
        """Limit queryset to the user's own tokens unless staff."""
        user = self.request.user
        if user.is_staff:
            return GovernanceToken.objects.all()
        return GovernanceToken.objects.filter(holder=user)
    
    @action(detail=True, methods=['post'])
    def delegate(self, request, pk=None):
        """Delegate voting power to another user."""
        token = self.get_object()
        
        if token.holder != request.user:
            return Response(
                {"detail": "You can only delegate your own tokens."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        delegate_id = request.data.get('delegate_id')
        if not delegate_id:
            return Response(
                {"detail": "Delegate ID is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth.models import User
            delegate = User.objects.get(id=delegate_id)
            token.delegate(delegate)
            return Response({"status": "tokens delegated"})
        except User.DoesNotExist:
            return Response(
                {"detail": "Delegate user not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def undelegate(self, request, pk=None):
        """Remove delegation."""
        token = self.get_object()
        
        if token.holder != request.user:
            return Response(
                {"detail": "You can only undelegate your own tokens."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        token.undelegate()
        return Response({"status": "delegation removed"})


class GuardianViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for guardians (read-only).
    """
    
    queryset = Guardian.objects.filter(is_active=True)
    serializer_class = GuardianSerializer
    permission_classes = [permissions.IsAuthenticated] 