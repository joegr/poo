"""
Serializers for the governance app.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Proposal, Vote, ProposalComment, GovernanceToken, 
    Guardian, Member, VerificationRequest, CircuitBreaker
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        """Meta options for the UserSerializer."""
        
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ProposalSerializer(serializers.ModelSerializer):
    """Serializer for Proposal model."""
    
    proposer = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        """Meta options for the ProposalSerializer."""
        
        model = Proposal
        fields = [
            'id', 'title', 'description', 'rationale', 'implementation_details',
            'timeline', 'proposer', 'status', 'status_display', 'created_at',
            'updated_at', 'discussion_start_time', 'voting_start_time',
            'voting_end_time', 'execution_time', 'content_document_id',
            'total_votes_for', 'total_votes_against', 'total_voting_power'
        ]
        read_only_fields = [
            'proposer', 'status', 'created_at', 'updated_at',
            'discussion_start_time', 'voting_start_time', 'voting_end_time',
            'execution_time', 'total_votes_for', 'total_votes_against',
            'total_voting_power'
        ]


class VoteSerializer(serializers.ModelSerializer):
    """Serializer for Vote model."""
    
    voter = UserSerializer(read_only=True)
    
    class Meta:
        """Meta options for the VoteSerializer."""
        
        model = Vote
        fields = [
            'id', 'proposal', 'voter', 'vote_count', 'vote_cost',
            'is_for', 'created_at'
        ]
        read_only_fields = ['voter', 'vote_cost', 'created_at']
    
    def validate(self, data):
        """Validate the vote data."""
        user = self.context['request'].user
        proposal = data['proposal']
        
        # Check if proposal is in voting phase
        if proposal.status != Proposal.Status.VOTING:
            raise serializers.ValidationError("This proposal is not in the voting phase.")
        
        # Check if user has already voted
        if Vote.objects.filter(proposal=proposal, voter=user).exists():
            raise serializers.ValidationError("You have already voted on this proposal.")
        
        # Check if user has enough voting power
        governance_token = GovernanceToken.objects.filter(holder=user).first()
        if not governance_token:
            raise serializers.ValidationError("You don't have any governance tokens.")
        
        vote_cost = Vote.calculate_vote_cost(data['vote_count'])
        if vote_cost > governance_token.balance:
            raise serializers.ValidationError(
                f"You don't have enough voting power. Required: {vote_cost}, Available: {governance_token.balance}"
            )
        
        # Check if vote exceeds maximum voting power percentage
        from django.conf import settings
        max_voting_power = proposal.total_voting_power * settings.MAX_VOTING_POWER_PERCENTAGE / 100
        if data['vote_count'] > max_voting_power:
            raise serializers.ValidationError(
                f"Your vote exceeds the maximum allowed voting power ({settings.MAX_VOTING_POWER_PERCENTAGE}%)."
            )
        
        return data
    
    def create(self, validated_data):
        """Create a new vote."""
        user = self.context['request'].user
        validated_data['voter'] = user
        
        # Lock tokens after voting
        governance_token = GovernanceToken.objects.get(holder=user)
        governance_token.lock_for_voting()
        
        return super().create(validated_data)


class ProposalCommentSerializer(serializers.ModelSerializer):
    """Serializer for ProposalComment model."""
    
    author = UserSerializer(read_only=True)
    
    class Meta:
        """Meta options for the ProposalCommentSerializer."""
        
        model = ProposalComment
        fields = ['id', 'proposal', 'author', 'content', 'created_at', 'updated_at']
        read_only_fields = ['author', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create a new comment."""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class GovernanceTokenSerializer(serializers.ModelSerializer):
    """Serializer for GovernanceToken model."""
    
    holder = UserSerializer(read_only=True)
    delegated_to = UserSerializer(read_only=True)
    
    class Meta:
        """Meta options for the GovernanceTokenSerializer."""
        
        model = GovernanceToken
        fields = [
            'id', 'holder', 'balance', 'locked_until', 'delegated_to', 'is_locked'
        ]
        read_only_fields = ['holder', 'locked_until', 'is_locked']


class GuardianSerializer(serializers.ModelSerializer):
    """Serializer for Guardian model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        """Meta options for the GuardianSerializer."""
        
        model = Guardian
        fields = ['id', 'user', 'term_start_date', 'term_end_date', 'is_active']
        read_only_fields = ['user']


class MemberSerializer(serializers.ModelSerializer):
    """Serializer for Member model."""
    
    user = UserSerializer(read_only=True)
    verification_status_display = serializers.CharField(source='get_verification_status_display', read_only=True)
    
    class Meta:
        """Meta options for the MemberSerializer."""
        
        model = Member
        fields = [
            'id', 'user', 'wallet_address', 'verification_status',
            'verification_status_display', 'join_date', 'reputation_score'
        ]
        read_only_fields = ['user', 'verification_status', 'join_date']


class VerificationRequestSerializer(serializers.ModelSerializer):
    """Serializer for VerificationRequest model."""
    
    user = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        """Meta options for the VerificationRequestSerializer."""
        
        model = VerificationRequest
        fields = [
            'id', 'user', 'full_name', 'date_of_birth', 'country',
            'id_document_type', 'id_document_number', 'document_front_image',
            'document_back_image', 'selfie_image', 'status', 'status_display',
            'rejection_reason', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'status', 'rejection_reason', 'created_at', 'updated_at']


class CircuitBreakerSerializer(serializers.ModelSerializer):
    """Serializer for CircuitBreaker model."""
    
    activated_by = UserSerializer(read_only=True)
    deactivated_by = UserSerializer(read_only=True)
    
    class Meta:
        """Meta options for the CircuitBreakerSerializer."""
        
        model = CircuitBreaker
        fields = [
            'id', 'is_active', 'activation_time', 'deactivation_time',
            'reason', 'activated_by', 'deactivated_by'
        ]
        read_only_fields = [
            'activation_time', 'deactivation_time', 'activated_by', 'deactivated_by'
        ] 