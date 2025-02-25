"""
Views for the governance app.
"""

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import User

from .models import (
    Proposal, Vote, ProposalComment, GovernanceToken, 
    Guardian, Member, VerificationRequest, CircuitBreaker
)
from .serializers import (
    ProposalSerializer, VoteSerializer, ProposalCommentSerializer,
    GovernanceTokenSerializer, GuardianSerializer, MemberSerializer,
    VerificationRequestSerializer, CircuitBreakerSerializer
)
from .permissions import (
    IsProposalOwnerOrReadOnly, IsVoteOwnerOrReadOnly, 
    IsCommentOwnerOrReadOnly, IsTokenOwnerOrReadOnly,
    IsGuardianOrReadOnly, IsMemberOrReadOnly
)


class ProposalViewSet(viewsets.ModelViewSet):
    """API endpoint for proposals."""
    
    queryset = Proposal.objects.all()
    serializer_class = ProposalSerializer
    permission_classes = [permissions.IsAuthenticated, IsProposalOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'proposer']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'total_votes_for', 'total_votes_against']
    
    def perform_create(self, serializer):
        """Set the proposer to the current user."""
        serializer.save(proposer=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start_discussion(self, request, pk=None):
        """Start the discussion phase for a proposal."""
        proposal = self.get_object()
        
        if proposal.status != Proposal.Status.DRAFT:
            return Response(
                {'detail': 'Proposal must be in DRAFT status to start discussion.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proposal.start_discussion()
        return Response({'status': proposal.status})
    
    @action(detail=True, methods=['post'])
    def start_voting(self, request, pk=None):
        """Start the voting phase for a proposal."""
        proposal = self.get_object()
        
        if proposal.status != Proposal.Status.DISCUSSION:
            return Response(
                {'detail': 'Proposal must be in DISCUSSION status to start voting.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate total voting power
        total_voting_power = GovernanceToken.objects.aggregate(
            total=Sum('balance')
        )['total'] or 0
        proposal.total_voting_power = total_voting_power
        
        proposal.start_voting()
        return Response({'status': proposal.status})
    
    @action(detail=True, methods=['post'])
    def end_voting(self, request, pk=None):
        """End the voting phase for a proposal."""
        proposal = self.get_object()
        
        if proposal.status != Proposal.Status.VOTING:
            return Response(
                {'detail': 'Proposal must be in VOTING status to end voting.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if voting period has ended
        if timezone.now() < proposal.voting_end_time:
            return Response(
                {'detail': 'Voting period has not ended yet.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = proposal.end_voting()
        return Response({'status': proposal.status, 'approved': result})
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute an approved proposal."""
        proposal = self.get_object()
        
        if proposal.status != Proposal.Status.APPROVED:
            return Response(
                {'detail': 'Proposal must be APPROVED to be executed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proposal.execute()
        return Response({'status': proposal.status})
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a proposal."""
        proposal = self.get_object()
        
        if proposal.status in [Proposal.Status.EXECUTED, Proposal.Status.REJECTED]:
            return Response(
                {'detail': 'Cannot cancel a proposal that has been executed or rejected.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        proposal.cancel()
        return Response({'status': proposal.status})


class VoteViewSet(viewsets.ModelViewSet):
    """API endpoint for votes."""
    
    queryset = Vote.objects.all()
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsVoteOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['proposal', 'voter', 'is_for']
    
    def perform_create(self, serializer):
        """Set the voter to the current user and validate voting rules."""
        proposal = serializer.validated_data['proposal']
        vote_count = serializer.validated_data['vote_count']
        is_for = serializer.validated_data.get('is_for', True)
        
        # Check if proposal is in voting phase
        if proposal.status != Proposal.Status.VOTING:
            raise serializers.ValidationError("Voting is not active for this proposal.")
        
        # Check if voting period has ended
        if timezone.now() > proposal.voting_end_time:
            raise serializers.ValidationError("Voting period has ended.")
        
        # Get user's governance tokens
        try:
            tokens = GovernanceToken.objects.get(holder=self.request.user)
        except GovernanceToken.DoesNotExist:
            raise serializers.ValidationError("You don't have any governance tokens.")
        
        # Check if user has enough tokens
        vote_cost = Vote.calculate_vote_cost(vote_count)
        if vote_cost > tokens.balance:
            raise serializers.ValidationError(
                f"Not enough tokens. Cost: {vote_cost}, Balance: {tokens.balance}"
            )
        
        # Check maximum voting power limit
        max_power_percentage = getattr(settings, 'MAX_VOTING_POWER_PERCENTAGE', 0.25)
        max_votes = int(proposal.total_voting_power * max_power_percentage)
        if vote_count > max_votes:
            raise serializers.ValidationError(
                f"Exceeds maximum voting power limit of {max_power_percentage * 100}%"
            )
        
        # Deduct tokens and lock them
        tokens.balance -= vote_cost
        tokens.lock_for_voting()
        tokens.save()
        
        serializer.save(voter=self.request.user, vote_cost=vote_cost)


class ProposalCommentViewSet(viewsets.ModelViewSet):
    """API endpoint for proposal comments."""
    
    queryset = ProposalComment.objects.all()
    serializer_class = ProposalCommentSerializer
    permission_classes = [permissions.IsAuthenticated, IsCommentOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['proposal', 'author']
    ordering_fields = ['created_at']
    
    def perform_create(self, serializer):
        """Set the author to the current user."""
        serializer.save(author=self.request.user)


class GovernanceTokenViewSet(viewsets.ModelViewSet):
    """API endpoint for governance tokens."""
    
    queryset = GovernanceToken.objects.all()
    serializer_class = GovernanceTokenSerializer
    permission_classes = [permissions.IsAuthenticated, IsTokenOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['holder']
    
    @action(detail=True, methods=['post'])
    def delegate(self, request, pk=None):
        """Delegate voting power to another user."""
        token = self.get_object()
        
        if token.is_locked:
            return Response(
                {'detail': 'Cannot delegate locked tokens.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        delegate_id = request.data.get('delegate_id')
        if not delegate_id:
            return Response(
                {'detail': 'Delegate ID is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            delegate = User.objects.get(id=delegate_id)
        except User.DoesNotExist:
            return Response(
                {'detail': 'Delegate user not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        token.delegate(delegate)
        return Response({'status': 'Delegation successful'})
    
    @action(detail=True, methods=['post'])
    def undelegate(self, request, pk=None):
        """Remove delegation."""
        token = self.get_object()
        
        if not token.delegated_to:
            return Response(
                {'detail': 'Token is not delegated.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token.undelegate()
        return Response({'status': 'Undelegation successful'})


class GuardianViewSet(viewsets.ModelViewSet):
    """API endpoint for guardians."""
    
    queryset = Guardian.objects.all()
    serializer_class = GuardianSerializer
    permission_classes = [permissions.IsAuthenticated, IsGuardianOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'user']


class MemberViewSet(viewsets.ModelViewSet):
    """API endpoint for DAO members."""
    
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated, IsMemberOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['verification_status', 'join_date']
    search_fields = ['user__username', 'wallet_address']


class VerificationRequestViewSet(viewsets.ModelViewSet):
    """API endpoint for verification requests."""
    
    queryset = VerificationRequest.objects.all()
    serializer_class = VerificationRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'user']
    ordering_fields = ['created_at', 'updated_at']
    
    def perform_create(self, serializer):
        """Set the user to the current user."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a verification request."""
        verification_request = self.get_object()
        
        if verification_request.status != VerificationRequest.Status.PENDING_REVIEW:
            return Response(
                {'detail': 'Can only approve pending requests.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update verification request
        verification_request.status = VerificationRequest.Status.APPROVED
        verification_request.save()
        
        # Update member status
        try:
            member = Member.objects.get(user=verification_request.user)
            member.verification_status = Member.VerificationStatus.VERIFIED
            member.save()
        except Member.DoesNotExist:
            pass
        
        return Response({'status': 'Verification approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a verification request."""
        verification_request = self.get_object()
        
        if verification_request.status != VerificationRequest.Status.PENDING_REVIEW:
            return Response(
                {'detail': 'Can only reject pending requests.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('rejection_reason')
        if not rejection_reason:
            return Response(
                {'detail': 'Rejection reason is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update verification request
        verification_request.status = VerificationRequest.Status.REJECTED
        verification_request.rejection_reason = rejection_reason
        verification_request.save()
        
        # Update member status
        try:
            member = Member.objects.get(user=verification_request.user)
            member.verification_status = Member.VerificationStatus.REJECTED
            member.save()
        except Member.DoesNotExist:
            pass
        
        return Response({'status': 'Verification rejected'})
    
    @action(detail=True, methods=['post'])
    def request_additional_info(self, request, pk=None):
        """Request additional information for a verification request."""
        verification_request = self.get_object()
        
        if verification_request.status != VerificationRequest.Status.PENDING_REVIEW:
            return Response(
                {'detail': 'Can only request additional info for pending requests.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        additional_info = request.data.get('additional_info')
        if not additional_info:
            return Response(
                {'detail': 'Additional info request details are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update verification request
        verification_request.status = VerificationRequest.Status.ADDITIONAL_INFO
        verification_request.rejection_reason = additional_info  # Reuse field for additional info
        verification_request.save()
        
        return Response({'status': 'Additional information requested'})


class CircuitBreakerViewSet(viewsets.ModelViewSet):
    """API endpoint for circuit breakers."""
    
    queryset = CircuitBreaker.objects.all()
    serializer_class = CircuitBreakerSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active']
    ordering_fields = ['activation_time']
    
    def perform_create(self, serializer):
        """Set the activated_by to the current user."""
        serializer.save(activated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a circuit breaker."""
        circuit_breaker = self.get_object()
        
        if not circuit_breaker.is_active:
            return Response(
                {'detail': 'Circuit breaker is already inactive.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        circuit_breaker.deactivate(request.user)
        return Response({'status': 'Circuit breaker deactivated'}) 