"""
Tests for the quadratic voting mechanism in the governance app.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from governance.models import Proposal, Vote, GovernanceToken


class QuadraticVotingTest(TestCase):
    """Test the quadratic voting mechanism."""

    def setUp(self):
        """Set up test data."""
        # Create users
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a proposal creator
        self.proposer = User.objects.create_user(
            username='proposer',
            email='proposer@example.com',
            password='password123'
        )
        
        # Give the user governance tokens
        self.token_balance = 100
        GovernanceToken.objects.create(
            holder=self.user,
            balance=self.token_balance
        )
        
        # Give proposer enough tokens to create a proposal
        GovernanceToken.objects.create(
            holder=self.proposer,
            balance=50  # Assuming this is enough (1% of total)
        )
        
        # Set up API client
        self.client = APIClient()
        
        # Create a proposal in VOTING status
        self.client.force_authenticate(user=self.proposer)
        proposal_data = {
            'title': 'Test Proposal',
            'description': 'This is a test proposal',
            'rationale': 'We need to test quadratic voting',
            'implementation_details': 'Implementation will be done after approval',
            'timeline': '7 days for implementation after approval'
        }
        
        response = self.client.post('/api/v1/governance/proposals/', proposal_data)
        self.proposal_id = response.data['id']
        
        # Move proposal to VOTING status
        proposal = Proposal.objects.get(id=self.proposal_id)
        proposal.status = Proposal.Status.VOTING
        proposal.save()
        
    def test_quadratic_voting_cost_calculation(self):
        """Test that voting cost is calculated correctly using the quadratic function."""
        self.client.force_authenticate(user=self.user)
        
        # Test different vote counts and their costs
        test_cases = [
            {'vote_count': 1, 'expected_cost': 1},
            {'vote_count': 2, 'expected_cost': 4},
            {'vote_count': 3, 'expected_cost': 9},
            {'vote_count': 5, 'expected_cost': 25},
            {'vote_count': 10, 'expected_cost': 100},
        ]
        
        for test_case in test_cases:
            # Get the cost calculation from the API
            response = self.client.get(f'/api/v1/governance/voting/cost_calculation/?vote_count={test_case["vote_count"]}')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data['credit_cost'], test_case['expected_cost'])
    
    def test_voting_deducts_correct_credits(self):
        """Test that casting votes deducts the correct number of credits."""
        self.client.force_authenticate(user=self.user)
        
        # Cast 5 votes (should cost 25 credits)
        vote_data = {
            'proposal': self.proposal_id,
            'vote_count': 5,
            'is_for': True
        }
        
        response = self.client.post('/api/v1/governance/votes/', vote_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the correct number of credits were deducted
        token = GovernanceToken.objects.get(holder=self.user)
        self.assertEqual(token.balance, self.token_balance - 25)
        
        # Check that the vote was recorded correctly
        vote = Vote.objects.get(voter=self.user, proposal_id=self.proposal_id)
        self.assertEqual(vote.vote_count, 5)
        self.assertTrue(vote.is_for)
    
    def test_insufficient_credits_for_voting(self):
        """Test that users cannot vote if they don't have enough credits."""
        self.client.force_authenticate(user=self.user)
        
        # Try to cast 11 votes (would cost 121 credits, more than the 100 available)
        vote_data = {
            'proposal': self.proposal_id,
            'vote_count': 11,
            'is_for': True
        }
        
        response = self.client.post('/api/v1/governance/votes/', vote_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that no credits were deducted
        token = GovernanceToken.objects.get(holder=self.user)
        self.assertEqual(token.balance, self.token_balance)
        
        # Check that no vote was recorded
        self.assertEqual(Vote.objects.filter(voter=self.user, proposal_id=self.proposal_id).count(), 0)
    
    def test_maximum_voting_power_limit(self):
        """Test that users cannot exceed the maximum voting power percentage."""
        self.client.force_authenticate(user=self.user)
        
        # Set the total voting power for the proposal
        total_voting_power = 400  # Assuming this is the total for all users
        max_percentage = 0.25  # 25% maximum
        max_votes = int((total_voting_power * max_percentage) ** 0.5)  # Square root of max credits
        
        # Mock the total voting power calculation
        with self.settings(TOTAL_VOTING_POWER=total_voting_power, MAX_VOTING_POWER_PERCENTAGE=max_percentage):
            # Try to cast more votes than allowed
            vote_data = {
                'proposal': self.proposal_id,
                'vote_count': max_votes + 1,  # One more than allowed
                'is_for': True
            }
            
            response = self.client.post('/api/v1/governance/votes/', vote_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            
            # Check that no credits were deducted
            token = GovernanceToken.objects.get(holder=self.user)
            self.assertEqual(token.balance, self.token_balance)
            
            # Now try with exactly the maximum allowed
            vote_data['vote_count'] = max_votes
            response = self.client.post('/api/v1/governance/votes/', vote_data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_token_locking_after_voting(self):
        """Test that tokens are locked after voting."""
        self.client.force_authenticate(user=self.user)
        
        # Cast 5 votes
        vote_data = {
            'proposal': self.proposal_id,
            'vote_count': 5,
            'is_for': True
        }
        
        response = self.client.post('/api/v1/governance/votes/', vote_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that tokens are locked
        token = GovernanceToken.objects.get(holder=self.user)
        self.assertTrue(token.is_locked)
        
        # Try to transfer tokens
        transfer_data = {
            'recipient': 'another_user',
            'amount': 10
        }
        
        response = self.client.post('/api/tokens/transfer/', transfer_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('locked', response.data['detail'].lower()) 