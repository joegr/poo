"""
Admin configuration for the treasury app.
"""

from django.contrib import admin
from .models import (
    Asset, AssetBalance, Transaction, TransactionApproval,
    TreasuryMetric, AllocationStrategy, AssetAllocation
)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    """Admin configuration for Asset model."""
    
    list_display = (
        'id', 'name', 'symbol', 'asset_type', 'is_stable',
        'risk_score', 'chain', 'created_at'
    )
    list_filter = ('asset_type', 'is_stable', 'chain', 'created_at')
    search_fields = ('name', 'symbol', 'description', 'contract_address')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'symbol', 'asset_type', 'description')
        }),
        ('Technical Details', {
            'fields': ('contract_address', 'chain', 'decimals')
        }),
        ('Risk Assessment', {
            'fields': ('risk_score', 'is_stable')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AssetBalance)
class AssetBalanceAdmin(admin.ModelAdmin):
    """Admin configuration for AssetBalance model."""
    
    list_display = ('id', 'asset', 'balance', 'usd_value', 'last_updated')
    list_filter = ('asset__asset_type', 'asset__is_stable', 'last_updated')
    search_fields = ('asset__name', 'asset__symbol')
    readonly_fields = ('last_updated',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin configuration for Transaction model."""
    
    list_display = (
        'id', 'asset', 'amount', 'usd_value', 'transaction_type',
        'status', 'proposer', 'created_at', 'executed_at'
    )
    list_filter = ('status', 'transaction_type', 'created_at', 'executed_at')
    search_fields = (
        'asset__name', 'asset__symbol', 'description',
        'transaction_hash', 'external_address', 'proposer__username'
    )
    readonly_fields = ('created_at', 'executed_at')
    fieldsets = (
        ('Transaction Details', {
            'fields': ('asset', 'amount', 'usd_value', 'transaction_type', 'status')
        }),
        ('Swap Details', {
            'fields': ('destination_asset', 'destination_amount'),
            'classes': ('collapse',)
        }),
        ('External Details', {
            'fields': ('transaction_hash', 'external_address', 'description')
        }),
        ('Metadata', {
            'fields': ('proposer', 'created_at', 'executed_at')
        }),
    )


@admin.register(TransactionApproval)
class TransactionApprovalAdmin(admin.ModelAdmin):
    """Admin configuration for TransactionApproval model."""
    
    list_display = ('id', 'transaction', 'guardian', 'approved', 'created_at')
    list_filter = ('approved', 'created_at')
    search_fields = ('transaction__asset__symbol', 'guardian__user__username', 'comments')
    readonly_fields = ('created_at',)


@admin.register(TreasuryMetric)
class TreasuryMetricAdmin(admin.ModelAdmin):
    """Admin configuration for TreasuryMetric model."""
    
    list_display = (
        'id', 'timestamp', 'total_value_usd', 'stable_assets_value_usd',
        'volatile_assets_value_usd', 'reserve_ratio', 'is_reserve_ratio_healthy'
    )
    list_filter = ('timestamp', 'is_reserve_ratio_healthy')
    readonly_fields = ('timestamp', 'is_reserve_ratio_healthy')


@admin.register(AllocationStrategy)
class AllocationStrategyAdmin(admin.ModelAdmin):
    """Admin configuration for AllocationStrategy model."""
    
    list_display = (
        'id', 'name', 'is_active', 'min_stable_assets_percentage',
        'max_single_asset_percentage', 'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Strategy Parameters', {
            'fields': ('min_stable_assets_percentage', 'max_single_asset_percentage', 'rebalance_threshold')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AssetAllocation)
class AssetAllocationAdmin(admin.ModelAdmin):
    """Admin configuration for AssetAllocation model."""
    
    list_display = ('id', 'strategy', 'asset_type', 'target_percentage')
    list_filter = ('strategy', 'asset_type')
    search_fields = ('strategy__name', 'asset_type') 