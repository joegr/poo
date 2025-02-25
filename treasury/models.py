"""
Models for the treasury app.
"""

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from governance.models import Guardian


class Asset(models.Model):
    """Model for treasury assets."""
    
    class AssetType(models.TextChoices):
        """Asset type choices."""
        
        CRYPTOCURRENCY = 'CRYPTO', 'Cryptocurrency'
        STABLECOIN = 'STABLE', 'Stablecoin'
        TOKEN = 'TOKEN', 'Token'
        NFT = 'NFT', 'Non-Fungible Token'
        REAL_ESTATE = 'REAL_ESTATE', 'Real Estate'
        EQUITY = 'EQUITY', 'Equity'
        BOND = 'BOND', 'Bond'
        OTHER = 'OTHER', 'Other'
    
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=50)
    asset_type = models.CharField(max_length=20, choices=AssetType.choices)
    description = models.TextField(blank=True)
    
    # Asset metadata
    contract_address = models.CharField(max_length=255, blank=True, null=True)
    chain = models.CharField(max_length=100, blank=True, null=True)
    decimals = models.PositiveIntegerField(default=18)
    
    # Risk assessment
    risk_score = models.PositiveIntegerField(default=50)  # 0-100 scale
    is_stable = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for the Asset model."""
        
        ordering = ['name']
        unique_together = ('symbol', 'contract_address', 'chain')
    
    def __str__(self):
        """String representation of the asset."""
        return f"{self.name} ({self.symbol})"


class AssetBalance(models.Model):
    """Model for treasury asset balances."""
    
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='balances')
    balance = models.DecimalField(max_digits=36, decimal_places=18, default=0)
    usd_value = models.DecimalField(max_digits=36, decimal_places=2, default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        """Meta options for the AssetBalance model."""
        
        ordering = ['-usd_value']
    
    def __str__(self):
        """String representation of the asset balance."""
        return f"{self.asset.symbol}: {self.balance} (${self.usd_value})"


class Transaction(models.Model):
    """Model for treasury transactions."""
    
    class Status(models.TextChoices):
        """Transaction status choices."""
        
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        EXECUTED = 'EXECUTED', 'Executed'
        FAILED = 'FAILED', 'Failed'
    
    class TransactionType(models.TextChoices):
        """Transaction type choices."""
        
        DEPOSIT = 'DEPOSIT', 'Deposit'
        WITHDRAWAL = 'WITHDRAWAL', 'Withdrawal'
        SWAP = 'SWAP', 'Swap'
        INVESTMENT = 'INVESTMENT', 'Investment'
        EXPENSE = 'EXPENSE', 'Expense'
        REVENUE = 'REVENUE', 'Revenue'
        OTHER = 'OTHER', 'Other'
    
    # Transaction details
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=36, decimal_places=18)
    usd_value = models.DecimalField(max_digits=36, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    # For swaps and transfers
    destination_asset = models.ForeignKey(
        Asset, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_transactions'
    )
    destination_amount = models.DecimalField(max_digits=36, decimal_places=18, null=True, blank=True)
    
    # External transaction details
    transaction_hash = models.CharField(max_length=255, blank=True, null=True)
    external_address = models.CharField(max_length=255, blank=True, null=True)
    
    # Metadata
    description = models.TextField(blank=True)
    proposer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='proposed_transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        """Meta options for the Transaction model."""
        
        ordering = ['-created_at']
    
    def __str__(self):
        """String representation of the transaction."""
        return f"{self.transaction_type}: {self.amount} {self.asset.symbol} (${self.usd_value})"
    
    def execute(self):
        """Execute the transaction."""
        if self.status != self.Status.APPROVED:
            return False
        
        try:
            # Update asset balance
            asset_balance, created = AssetBalance.objects.get_or_create(asset=self.asset)
            
            if self.transaction_type in [self.TransactionType.DEPOSIT, self.TransactionType.REVENUE]:
                asset_balance.balance += self.amount
                asset_balance.usd_value += self.usd_value
            elif self.transaction_type in [self.TransactionType.WITHDRAWAL, self.TransactionType.EXPENSE]:
                asset_balance.balance -= self.amount
                asset_balance.usd_value -= self.usd_value
            elif self.transaction_type == self.TransactionType.SWAP and self.destination_asset:
                # Decrease source asset
                asset_balance.balance -= self.amount
                asset_balance.usd_value -= self.usd_value
                
                # Increase destination asset
                dest_balance, created = AssetBalance.objects.get_or_create(asset=self.destination_asset)
                dest_balance.balance += self.destination_amount
                dest_balance.usd_value += self.usd_value  # Assuming same USD value for simplicity
                dest_balance.save()
            
            asset_balance.save()
            
            # Update transaction status
            self.status = self.Status.EXECUTED
            self.executed_at = timezone.now()
            self.save()
            
            return True
        except Exception as e:
            self.status = self.Status.FAILED
            self.save()
            return False


class TransactionApproval(models.Model):
    """Model for multi-signature transaction approvals."""
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='approvals')
    guardian = models.ForeignKey(Guardian, on_delete=models.CASCADE, related_name='approvals')
    approved = models.BooleanField(default=True)
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        """Meta options for the TransactionApproval model."""
        
        unique_together = ('transaction', 'guardian')
        ordering = ['created_at']
    
    def __str__(self):
        """String representation of the transaction approval."""
        action = "approved" if self.approved else "rejected"
        return f"{self.guardian.user.username} {action} transaction {self.transaction.id}"
    
    def save(self, *args, **kwargs):
        """Override save to check for threshold and execute transaction if reached."""
        super().save(*args, **kwargs)
        
        # Check if threshold is reached
        transaction = self.transaction
        if transaction.status == Transaction.Status.PENDING:
            approvals = TransactionApproval.objects.filter(
                transaction=transaction, approved=True
            ).count()
            
            if approvals >= settings.TREASURY_MULTISIG_THRESHOLD:
                transaction.status = Transaction.Status.APPROVED
                transaction.save()
                transaction.execute()


class TreasuryMetric(models.Model):
    """Model for treasury metrics."""
    
    timestamp = models.DateTimeField(auto_now_add=True)
    total_value_usd = models.DecimalField(max_digits=36, decimal_places=2, default=0)
    stable_assets_value_usd = models.DecimalField(max_digits=36, decimal_places=2, default=0)
    volatile_assets_value_usd = models.DecimalField(max_digits=36, decimal_places=2, default=0)
    reserve_ratio = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    
    class Meta:
        """Meta options for the TreasuryMetric model."""
        
        ordering = ['-timestamp']
    
    def __str__(self):
        """String representation of the treasury metric."""
        return f"Treasury Metric: ${self.total_value_usd} at {self.timestamp}"
    
    @property
    def is_reserve_ratio_healthy(self):
        """Check if reserve ratio is above the minimum threshold."""
        return self.reserve_ratio >= settings.TREASURY_RESERVE_RATIO


class AllocationStrategy(models.Model):
    """Model for treasury allocation strategies."""
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Strategy parameters
    min_stable_assets_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)
    max_single_asset_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=20.00)
    rebalance_threshold = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    
    class Meta:
        """Meta options for the AllocationStrategy model."""
        
        verbose_name_plural = "Allocation Strategies"
        ordering = ['-is_active', 'name']
    
    def __str__(self):
        """String representation of the allocation strategy."""
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} ({status})"


class AssetAllocation(models.Model):
    """Model for asset allocations within a strategy."""
    
    strategy = models.ForeignKey(AllocationStrategy, on_delete=models.CASCADE, related_name='allocations')
    asset_type = models.CharField(max_length=20, choices=Asset.AssetType.choices)
    target_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    
    class Meta:
        """Meta options for the AssetAllocation model."""
        
        unique_together = ('strategy', 'asset_type')
        ordering = ['-target_percentage']
    
    def __str__(self):
        """String representation of the asset allocation."""
        return f"{self.strategy.name}: {self.asset_type} - {self.target_percentage}%" 