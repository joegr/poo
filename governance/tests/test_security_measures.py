"""
Tests for security measures in the governance app.
"""

from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
import time
from unittest.mock import patch

from governance.models import Member, Guardian, CircuitBreaker
from treasury.models import TreasuryTransaction


class SecurityMeasuresTest(TestCase):
    """Test security measures for the governance system."""

    def setUp(self):
        """Set up test data."""
        # Create a regular user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123'
        )
        
        # Create a guardian
        self.guardian = User.objects.create_user(
            username='guardian',
            email='guardian@example.com',
            password='password123'
        )
        
        Guardian.objects.create(
            user=self.guardian,
            term_start_date='2023-01-01',
            term_end_date='2023-04-01'
        )
        
        # Create a new member
        self.new_member = User.objects.create_user(
            username='newmember',
            email='newmember@example.com',
            password='password123'
        )
        
        Member.objects.create(
            user=self.new_member,
            wallet_address='0x1234567890abcdef1234567890abcdef12345678',
            verification_status=Member.VerificationStatus.VERIFIED,
            join_date='2023-01-01'
        )
        
        # Set up API client
        self.client = APIClient()
        
        # Create transaction data for testing circuit breaker
        self.transaction_data = {
            'asset': 'ETH',
            'amount': 10.0,
            'transaction_type': 'WITHDRAWAL',
            'description': 'Fund development grant',
            'recipient_address': '0x1234567890abcdef1234567890abcdef12345678'
        }
    
    def test_multi_factor_authentication_for_guardians(self):
        """Test that guardians require multi-factor authentication for critical operations."""
        self.client.force_authenticate(user=self.guardian)
        
        # Create a transaction
        response = self.client.post('/api/v1/treasury/transactions/', self.transaction_data)
        transaction_id = response.data['id']
        
        # Try to approve without MFA
        response = self.client.post(f'/api/v1/treasury/transactions/{transaction_id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('multi-factor authentication required', response.data['detail'].lower())
        
        # Provide MFA code
        mfa_data = {
            'mfa_code': '123456'  # In a real test, we'd mock the MFA verification
        }
        
        # Mock the MFA verification
        with patch('governance.services.mfa_service.verify_mfa_code', return_value=True):
            response = self.client.post(
                f'/api/v1/treasury/transactions/{transaction_id}/approve/',
                mfa_data
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    @override_settings(RATE_LIMIT_PER_MINUTE=5)
    def test_rate_limiting(self):
        """Test that API requests are rate limited."""
        self.client.force_authenticate(user=self.user)
        
        # Make requests up to the limit
        for _ in range(5):
            response = self.client.get('/api/v1/governance/proposals/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # The next request should be rate limited
        response = self.client.get('/api/v1/governance/proposals/')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn('retry-after', response.headers)
    
    def test_gradual_voting_power_increase(self):
        """Test that new members have limited voting power that increases over time."""
        self.client.force_authenticate(user=self.new_member)
        
        # Check initial voting power cap (should be 5%)
        response = self.client.get('/api/v1/governance/members/me/voting_power/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['max_voting_power_percentage'], 0.05)
        
        # Simulate 3 months of activity
        member = Member.objects.get(user=self.new_member)
        member.join_date = '2022-10-01'  # 3 months ago
        member.save()
        
        # Check voting power cap after 3 months (should be 10%)
        response = self.client.get('/api/v1/governance/members/me/voting_power/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['max_voting_power_percentage'], 0.10)
        
        # Simulate 6 months of activity
        member.join_date = '2022-07-01'  # 6 months ago
        member.save()
        
        # Check voting power cap after 6 months (should be 25%)
        response = self.client.get('/api/v1/governance/members/me/voting_power/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['max_voting_power_percentage'], 0.25)
    
    def test_circuit_breaker_activation(self):
        """Test that the circuit breaker is activated when unusual activity is detected."""
        # Create multiple transactions to simulate unusual activity
        self.client.force_authenticate(user=self.user)
        
        # Create a large transaction (21% of treasury value)
        large_transaction_data = self.transaction_data.copy()
        large_transaction_data['amount'] = 210.0  # Assuming treasury value is 1000 ETH
        
        # Mock the treasury value and circuit breaker service
        with patch('governance.services.treasury_service.get_treasury_value', return_value=1000.0):
            with patch('governance.services.circuit_breaker_service.check_transaction_threshold', return_value=True):
                response = self.client.post('/api/v1/treasury/transactions/', large_transaction_data)
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                
                # Check that the circuit breaker was activated
                circuit_breaker = CircuitBreaker.objects.latest('activation_time')
                self.assertTrue(circuit_breaker.is_active)
                self.assertEqual(circuit_breaker.reason, 'Large transaction detected')
                
                # Try to execute another transaction while circuit breaker is active
                response = self.client.post('/api/v1/treasury/transactions/', self.transaction_data)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                self.assertIn('circuit breaker is active', response.data['detail'].lower())
    
    def test_secure_session_management(self):
        """Test that sessions are managed securely."""
        # Login
        response = self.client.post('/api/v1/auth/login/', {
            'username': 'testuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that the session cookie has secure attributes
        session_cookie = response.cookies.get('sessionid')
        self.assertTrue(session_cookie['secure'])
        self.assertTrue(session_cookie['httponly'])
        
        # Check session timeout
        with override_settings(SESSION_COOKIE_AGE=1):  # 1 second timeout for testing
            response = self.client.post('/api/v1/auth/login/', {
                'username': 'testuser',
                'password': 'password123'
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Wait for session to expire
            time.sleep(2)
            
            # Try to access a protected endpoint
            response = self.client.get('/api/v1/governance/members/me/')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED) 