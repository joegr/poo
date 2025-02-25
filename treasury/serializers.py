"""
Serializers for the treasury app.
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from governance.serializers import UserSerializer, GuardianSerializer
from .models import (
    Asset, AssetBalance, Transaction, TransactionApproval,
    TreasuryMetric, AllocationStrategy, AssetAllocation
)


class AssetSerializer(serializers.ModelSerializer):
    """Serializer for Asset model."""
    
    asset_type_display = serializers.CharField(source='get_asset_type_display', read_only=True)
    
    class Meta:
        """Meta options for the AssetSerializer."""
        
        model = Asset
        fields = [
            'id', 'name', 'symbol', 'asset_type', 'asset_type_display', 'description',
            'contract_address', 'chain', 'decimals', 'risk_score', 'is_stable',
            'created_at', 'updated_at'
        ]


class AssetBalanceSerializer(serializers.ModelSerializer):
    """Serializer for AssetBalance model."""
    
    asset = AssetSerializer(read_only=True)
    
    class Meta:
        """Meta options for the AssetBalanceSerializer."""
        
        model = AssetBalance
        fields = ['id', 'asset', 'balance', 'usd_value', 'last_updated']


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model."""
    
    asset = AssetSerializer(read_only=True)
    destination_asset = AssetSerializer(read_only=True)
    proposer = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    approval_count = serializers.SerializerMethodField()
    
    class Meta:
        """Meta options for the TransactionSerializer."""
        
        model = Transaction
        fields = [
            'id', 'asset', 'amount', 'usd_value', 'transaction_type', 'transaction_type_display',
            'status', 'status_display', 'destination_asset', 'destination_amount',
            'transaction_hash', 'external_address', 'description', 'proposer',
            'created_at', 'executed_at', 'approval_count'
        ]
        read_only_fields = ['status', 'executed_at', 'approval_count']
    
    def get_approval_count(self, obj):
        """Get the number of approvals for this transaction."""
        return obj.approvals.filter(approved=True).count()
    
    def create(self, validated_data):
        """Create a new transaction."""
        validated_data['proposer'] = self.context['request'].user
        return super().create(validated_data)


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions."""
    
    asset_id = serializers.IntegerField(write_only=True)
    destination_asset_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        """Meta options for the TransactionCreateSerializer."""
        
        model = Transaction
        fields = [
            'asset_id', 'amount', 'usd_value', 'transaction_type',
            'destination_asset_id', 'destination_amount',
            'transaction_hash', 'external_address', 'description'
        ]
    
    def create(self, validated_data):
        """Create a new transaction."""
        asset_id = validated_data.pop('asset_id')
        destination_asset_id = validated_data.pop('destination_asset_id', None)
        
        # Get the asset objects
        asset = Asset.objects.get(id=asset_id)
        destination_asset = None
        if destination_asset_id:
            destination_asset = Asset.objects.get(id=destination_asset_id)
        
        # Create the transaction
        transaction = Transaction.objects.create(
            asset=asset,
            destination_asset=destination_asset,
            proposer=self.context['request'].user,
            **validated_data
        )
        
        return transaction


class TransactionApprovalSerializer(serializers.ModelSerializer):
    """Serializer for TransactionApproval model."""
    
    guardian = GuardianSerializer(read_only=True)
    transaction = TransactionSerializer(read_only=True)
    
    class Meta:
        """Meta options for the TransactionApprovalSerializer."""
        
        model = TransactionApproval
        fields = ['id', 'transaction', 'guardian', 'approved', 'comments', 'created_at']
        read_only_fields = ['created_at']
    
    def create(self, validated_data):
        """Create a new transaction approval."""
        # Get the guardian for the current user
        from governance.models import Guardian
        guardian = Guardian.objects.get(user=self.context['request'].user)
        
        # Create the approval
        approval = TransactionApproval.objects.create(
            guardian=guardian,
            **validated_data
        )
        
        return approval


class TransactionApprovalCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transaction approvals."""
    
    transaction_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        """Meta options for the TransactionApprovalCreateSerializer."""
        
        model = TransactionApproval
        fields = ['transaction_id', 'approved', 'comments']
    
    def create(self, validated_data):
        """Create a new transaction approval."""
        transaction_id = validated_data.pop('transaction_id')
        
        # Get the transaction
        transaction = Transaction.objects.get(id=transaction_id)
        
        # Get the guardian for the current user
        from governance.models import Guardian
        guardian = Guardian.objects.get(user=self.context['request'].user)
        
        # Create the approval
        approval = TransactionApproval.objects.create(
            transaction=transaction,
            guardian=guardian,
            **validated_data
        )
        
        return approval


class TreasuryMetricSerializer(serializers.ModelSerializer):
    """Serializer for TreasuryMetric model."""
    
    is_reserve_ratio_healthy = serializers.BooleanField(read_only=True)
    
    class Meta:
        """Meta options for the TreasuryMetricSerializer."""
        
        model = TreasuryMetric
        fields = [
            'id', 'timestamp', 'total_value_usd', 'stable_assets_value_usd',
            'volatile_assets_value_usd', 'reserve_ratio', 'is_reserve_ratio_healthy'
        ]
        read_only_fields = ['timestamp', 'is_reserve_ratio_healthy']


class AssetAllocationSerializer(serializers.ModelSerializer):
    """Serializer for AssetAllocation model."""
    
    asset_type_display = serializers.CharField(source='get_asset_type_display', read_only=True)
    
    class Meta:
        """Meta options for the AssetAllocationSerializer."""
        
        model = AssetAllocation
        fields = ['id', 'asset_type', 'asset_type_display', 'target_percentage']


class AllocationStrategySerializer(serializers.ModelSerializer):
    """Serializer for AllocationStrategy model."""
    
    allocations = AssetAllocationSerializer(many=True, read_only=True)
    
    class Meta:
        """Meta options for the AllocationStrategySerializer."""
        
        model = AllocationStrategy
        fields = [
            'id', 'name', 'description', 'is_active', 'created_at', 'updated_at',
            'min_stable_assets_percentage', 'max_single_asset_percentage',
            'rebalance_threshold', 'allocations'
        ]
        read_only_fields = ['created_at', 'updated_at'] 