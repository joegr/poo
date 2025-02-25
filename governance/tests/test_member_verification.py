"""
Tests for member identity verification in the governance app.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from governance.models import Member, VerificationRequest, Proposal, Vote


class MemberVerificationTest(TestCase):
    """Test member identity verification process."""

    def setUp(self):
        """Set up test data."""
        # Create a user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a verification officer
        self.officer = User.objects.create_user(
            username='officer',
            email='officer@example.com',
            password='password123'
        )
        self.officer.is_staff = True
        self.officer.save()
        
        # Set up API client
        self.client = APIClient()
        
        # Create registration data
        self.registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'wallet_address': '0x1234567890abcdef1234567890abcdef12345678'
        }
        
        # Create verification data
        self.verification_data = {
            'full_name': 'Alice Johnson',
            'date_of_birth': '1990-01-15',
            'country': 'United States',
            'id_document_type': 'Passport',
            'id_document_number': 'AB123456',
            'document_front_image': 'base64encodedimage1',
            'document_back_image': 'base64encodedimage2',
            'selfie_image': 'base64encodedimage3'
        }
    
    def test_register_new_member(self):
        """Test registering a new member."""
        response = self.client.post('/api/v1/governance/members/register/', self.registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        
        # Check that a member profile was created
        member = Member.objects.get(user=user)
        self.assertEqual(member.wallet_address, '0x1234567890abcdef1234567890abcdef12345678')
        self.assertEqual(member.verification_status, Member.VerificationStatus.UNVERIFIED)
    
    def test_submit_verification_request(self):
        """Test submitting a verification request."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.post('/api/v1/governance/members/verify/', self.verification_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that a verification request was created
        verification_request = VerificationRequest.objects.get(user=self.user)
        self.assertEqual(verification_request.full_name, 'Alice Johnson')
        self.assertEqual(verification_request.id_document_number, 'AB123456')
        self.assertEqual(verification_request.status, VerificationRequest.Status.PENDING_REVIEW)
        
        # Check that the member status was updated
        member = Member.objects.get(user=self.user)
        self.assertEqual(member.verification_status, Member.VerificationStatus.PENDING)
    
    def test_approve_verification_request(self):
        """Test approving a verification request."""
        # Create a verification request
        self.client.force_authenticate(user=self.user)
        self.client.post('/api/v1/governance/members/verify/', self.verification_data)
        
        # Get the verification request
        verification_request = VerificationRequest.objects.get(user=self.user)
        
        # Approve the request as an officer
        self.client.force_authenticate(user=self.officer)
        response = self.client.post(f'/api/admin/verification/{verification_request.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the verification request was approved
        verification_request.refresh_from_db()
        self.assertEqual(verification_request.status, VerificationRequest.Status.APPROVED)
        
        # Check that the member status was updated
        member = Member.objects.get(user=self.user)
        self.assertEqual(member.verification_status, Member.VerificationStatus.VERIFIED)
    
    def test_reject_verification_request(self):
        """Test rejecting a verification request."""
        # Create a verification request
        self.client.force_authenticate(user=self.user)
        self.client.post('/api/v1/governance/members/verify/', self.verification_data)
        
        # Get the verification request
        verification_request = VerificationRequest.objects.get(user=self.user)
        
        # Reject the request as an officer
        self.client.force_authenticate(user=self.officer)
        rejection_data = {
            'reason': 'Documents unclear'
        }
        response = self.client.post(f'/api/admin/verification/{verification_request.id}/reject/', rejection_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the verification request was rejected
        verification_request.refresh_from_db()
        self.assertEqual(verification_request.status, VerificationRequest.Status.REJECTED)
        self.assertEqual(verification_request.rejection_reason, 'Documents unclear')
        
        # Check that the member status was updated
        member = Member.objects.get(user=self.user)
        self.assertEqual(member.verification_status, Member.VerificationStatus.REJECTED)
    
    def test_unverified_member_cannot_vote(self):
        """Test that unverified members cannot vote on proposals."""
        # Create a proposal
        proposal = Proposal.objects.create(
            title='Test Proposal',
            description='This is a test proposal',
            status=Proposal.Status.VOTING
        )
        
        # Try to vote as an unverified member
        self.client.force_authenticate(user=self.user)
        vote_data = {
            'proposal': proposal.id,
            'vote_count': 1,
            'is_for': True
        }
        response = self.client.post('/api/votes/', vote_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Verify the member
        member = Member.objects.get_or_create(user=self.user)[0]
        member.verification_status = Member.VerificationStatus.VERIFIED
        member.save()
        
        # Try to vote again
        response = self.client.post('/api/votes/', vote_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that the vote was recorded
        vote = Vote.objects.get(voter=self.user, proposal=proposal)
        self.assertEqual(vote.vote_count, 1)
        self.assertTrue(vote.is_for) 