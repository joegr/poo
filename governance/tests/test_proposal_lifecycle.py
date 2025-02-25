"""
Tests for the proposal lifecycle in the governance app.
"""

import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from governance.models import Proposal, Vote, GovernanceToken


class ProposalLifecycleTest(TestCase):
    """Test the complete lifecycle of a proposal."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.proposer = User.objects.create_user(
            username='proposer',
            email='proposer@example.com',
            password='password123'
        )
        
        # Create voters
        self.voters = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'voter{i}',
                email=f'voter{i}@example.com',
                password='password123'
            )
            self.voters.append(user)
            
            # Give each voter some governance tokens
            GovernanceToken.objects.create(
                holder=user,
                balance=100  # Each voter has 100 tokens/voting credits
            )
        
        # Give proposer enough tokens to create a proposal (1% of total)
        total_tokens = 100 * len(self.voters)  # 1000 tokens total
        min_tokens_needed = total_tokens * 0.01  # 1% of total
        
        GovernanceToken.objects.create(
            holder=self.proposer,
            balance=int(min_tokens_needed)
        )
        
        # Set up API client
        self.client = APIClient()
        
        # Create a proposal
        self.proposal_data = {
            'title': 'Test Proposal',
            'description': 'This is a test proposal',
            'rationale': 'We need to test the proposal lifecycle',
            'implementation_details': 'Implementation will be done after approval',
            'timeline': '7 days for implementation after approval'
        }
        
    def test_complete_proposal_lifecycle(self):
        """Test the complete lifecycle of a proposal from creation to execution."""
        # 1. Create a proposal
        self.client.force_authenticate(user=self.proposer)
        response = self.client.post('/api/v1/governance/proposals/', self.proposal_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        proposal_id = response.data['id']
        proposal = Proposal.objects.get(id=proposal_id)
        self.assertEqual(proposal.status, Proposal.Status.DRAFT)
        
        # 2. Start discussion period
        response = self.client.post(f'/api/v1/governance/proposals/{proposal_id}/start_discussion/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, Proposal.Status.DISCUSSION)
        self.assertIsNotNone(proposal.discussion_start_time)
        
        # 3. Start voting period (after discussion period)
        # Fast-forward time by setting discussion_start_time to 15 days ago
        proposal.discussion_start_time = timezone.now() - datetime.timedelta(days=15)
        proposal.save()
        
        response = self.client.post(f'/api/v1/governance/proposals/{proposal_id}/start_voting/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, Proposal.Status.VOTING)
        self.assertIsNotNone(proposal.voting_start_time)
        
        # 4. Cast votes
        # We need at least 45% participation and 70% approval
        total_voting_power = 100 * len(self.voters)  # 1000 total
        min_participation = total_voting_power * 0.45  # 450 minimum
        
        votes_for = 0
        votes_against = 0
        voting_power_used = 0
        
        # Have 7 voters vote in favor (70%)
        for i in range(7):
            self.client.force_authenticate(user=self.voters[i])
            vote_data = {
                'proposal': proposal_id,
                'vote_count': 5,  # Each voter casts 5 votes (costs 25 credits)
                'is_for': True
            }
            response = self.client.post('/api/v1/governance/votes/', vote_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            votes_for += 5
            voting_power_used += 25
        
        # Have 3 voters vote against (30%)
        for i in range(7, 10):
            self.client.force_authenticate(user=self.voters[i])
            vote_data = {
                'proposal': proposal_id,
                'vote_count': 5,  # Each voter casts 5 votes (costs 25 credits)
                'is_for': False
            }
            response = self.client.post('/api/v1/governance/votes/', vote_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            
            votes_against += 5
            voting_power_used += 25
        
        # 5. End voting period
        # Fast-forward time by setting voting_start_time to 8 days ago
        self.client.force_authenticate(user=self.proposer)
        proposal.voting_start_time = timezone.now() - datetime.timedelta(days=8)
        proposal.save()
        
        response = self.client.post(f'/api/v1/governance/proposals/{proposal_id}/end_voting/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, Proposal.Status.APPROVED)
        self.assertEqual(proposal.total_votes_for, votes_for)
        self.assertEqual(proposal.total_votes_against, votes_against)
        
        # Verify that we met quorum and approval threshold
        self.assertGreaterEqual(voting_power_used, min_participation)
        self.assertGreaterEqual(votes_for / (votes_for + votes_against), 0.7)
        
        # 6. Execute the proposal
        # Fast-forward time by setting voting_end_time to 3 days ago (after timelock)
        proposal.voting_end_time = timezone.now() - datetime.timedelta(days=3)
        proposal.save()
        
        response = self.client.post(f'/api/v1/governance/proposals/{proposal_id}/execute/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, Proposal.Status.EXECUTED)
        self.assertIsNotNone(proposal.execution_time) 