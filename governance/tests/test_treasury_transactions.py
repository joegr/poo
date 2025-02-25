"""
Tests for treasury transaction management in the governance app.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status

from governance.models import Guardian
from treasury.models import TreasuryTransaction


class TreasuryTransactionTest(TestCase):
    """Test treasury transaction creation, approval, and execution."""

    def setUp(self):
        """Set up test data."""
        # Create a regular member
        self.member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='password123'
        )
        
        # Create guardians
        self.guardians = []
        for i in range(9):
            user = User.objects.create_user(
                username=f'guardian{i}',
                email=f'guardian{i}@example.com',
                password='password123'
            )
            self.guardians.append(user)
            
            # Make them guardians
            Guardian.objects.create(
                user=user,
                term_start_date='2023-01-01',
                term_end_date='2023-04-01'
            )
        
        # Set up API client
        self.client = APIClient()
        
        # Create transaction data
        self.transaction_data = {
            'asset': 'ETH',
            'amount': 10.0,
            'transaction_type': 'WITHDRAWAL',
            'description': 'Fund development grant',
            'recipient_address': '0x1234567890abcdef1234567890abcdef12345678'
        }
    
    def test_create_treasury_transaction(self):
        """Test creating a treasury transaction proposal."""
        self.client.force_authenticate(user=self.member)
        
        response = self.client.post('/api/v1/treasury/transactions/', self.transaction_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        transaction_id = response.data['id']
        transaction = TreasuryTransaction.objects.get(id=transaction_id)
        
        self.assertEqual(transaction.status, TreasuryTransaction.Status.PENDING)
        self.assertEqual(transaction.asset, 'ETH')
        self.assertEqual(transaction.amount, 10.0)
        self.assertEqual(transaction.transaction_type, 'WITHDRAWAL')
        self.assertEqual(transaction.description, 'Fund development grant')
        self.assertEqual(transaction.approval_count, 0)
        self.assertEqual(transaction.rejection_count, 0)
    
    def test_guardian_approval_process(self):
        """Test the guardian approval process for a treasury transaction."""
        # Create a transaction
        self.client.force_authenticate(user=self.member)
        response = self.client.post('/api/v1/treasury/transactions/', self.transaction_data)
        transaction_id = response.data['id']
        
        # Have 5 guardians approve the transaction (threshold for execution)
        for i in range(5):
            self.client.force_authenticate(user=self.guardians[i])
            response = self.client.post(f'/api/treasury/transactions/{transaction_id}/approve/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the transaction is now approved
        transaction = TreasuryTransaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.approval_count, 5)
        self.assertEqual(transaction.status, TreasuryTransaction.Status.APPROVED)
        
        # Execute the transaction
        response = self.client.post(f'/api/treasury/transactions/{transaction_id}/execute/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the transaction is now executed
        transaction.refresh_from_db()
        self.assertEqual(transaction.status, TreasuryTransaction.Status.EXECUTED)
    
    def test_guardian_rejection_process(self):
        """Test the guardian rejection process for a treasury transaction."""
        # Create a transaction
        self.client.force_authenticate(user=self.member)
        response = self.client.post('/api/v1/treasury/transactions/', self.transaction_data)
        transaction_id = response.data['id']
        
        # Have 5 guardians reject the transaction
        for i in range(5):
            self.client.force_authenticate(user=self.guardians[i])
            rejection_data = {
                'reason': 'Excessive spending'
            }
            response = self.client.post(f'/api/treasury/transactions/{transaction_id}/reject/', rejection_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the transaction is now rejected
        transaction = TreasuryTransaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.rejection_count, 5)
        self.assertEqual(transaction.status, TreasuryTransaction.Status.REJECTED)
        
        # Try to execute the transaction (should fail)
        response = self.client.post(f'/api/treasury/transactions/{transaction_id}/execute/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_non_guardian_cannot_approve(self):
        """Test that non-guardians cannot approve transactions."""
        # Create a transaction
        self.client.force_authenticate(user=self.member)
        response = self.client.post('/api/v1/treasury/transactions/', self.transaction_data)
        transaction_id = response.data['id']
        
        # Try to approve as a non-guardian
        response = self.client.post(f'/api/treasury/transactions/{transaction_id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Check that the transaction approval count is still 0
        transaction = TreasuryTransaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.approval_count, 0)
    
    def test_guardian_cannot_approve_twice(self):
        """Test that a guardian cannot approve the same transaction twice."""
        # Create a transaction
        self.client.force_authenticate(user=self.member)
        response = self.client.post('/api/v1/treasury/transactions/', self.transaction_data)
        transaction_id = response.data['id']
        
        # Approve as a guardian
        self.client.force_authenticate(user=self.guardians[0])
        response = self.client.post(f'/api/treasury/transactions/{transaction_id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to approve again
        response = self.client.post(f'/api/treasury/transactions/{transaction_id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Check that the transaction approval count is still 1
        transaction = TreasuryTransaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.approval_count, 1) 