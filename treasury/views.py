"""
Views for the treasury app.
"""

from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Sum
from django.utils import timezone

from .models import (
    Asset, AssetBalance, TreasuryTransaction, TransactionApproval,
    TreasuryMetric, AllocationStrategy, AssetAllocation
)
from .serializers import (
    AssetSerializer, AssetBalanceSerializer, TreasuryTransactionSerializer,
    TransactionApprovalSerializer, TreasuryMetricSerializer,
    AllocationStrategySerializer, AssetAllocationSerializer,
    TransactionApprovalCreateSerializer, TransactionCreateSerializer
)
from governance.models import Guardian


class IsGuardianOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow guardians to create/edit objects.
    """
    
    def has_permission(self, request, view):
        # Read permissions are allowed to any authenticated request
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions are only allowed to guardians
        return request.user and request.user.is_authenticated and hasattr(request.user, 'guardian')


class AssetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for assets.
    """
    
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated, IsGuardianOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['asset_type', 'is_stable', 'chain']
    search_fields = ['name', 'symbol', 'description']
    ordering_fields = ['name', 'symbol', 'risk_score', 'created_at']
    ordering = ['name']


class AssetBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for asset balances (read-only).
    """
    
    queryset = AssetBalance.objects.all()
    serializer_class = AssetBalanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['asset__asset_type', 'asset__is_stable']
    ordering_fields = ['balance', 'usd_value', 'last_updated']
    ordering = ['-usd_value']
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get a summary of all asset balances."""
        total_value = AssetBalance.objects.aggregate(total=Sum('usd_value'))['total'] or 0
        stable_value = AssetBalance.objects.filter(
            asset__is_stable=True
        ).aggregate(total=Sum('usd_value'))['total'] or 0
        volatile_value = total_value - stable_value
        
        # Calculate reserve ratio
        reserve_ratio = 0
        if total_value > 0:
            reserve_ratio = stable_value / total_value
        
        # Create or update treasury metric
        TreasuryMetric.objects.create(
            total_value_usd=total_value,
            stable_assets_value_usd=stable_value,
            volatile_assets_value_usd=volatile_value,
            reserve_ratio=reserve_ratio
        )
        
        return Response({
            'total_value_usd': total_value,
            'stable_assets_value_usd': stable_value,
            'volatile_assets_value_usd': volatile_value,
            'reserve_ratio': reserve_ratio,
            'asset_count': AssetBalance.objects.count()
        })


class TreasuryTransactionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for transactions.
    """
    
    queryset = TreasuryTransaction.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'transaction_type', 'asset', 'proposer']
    search_fields = ['description', 'transaction_hash', 'external_address']
    ordering_fields = ['created_at', 'executed_at', 'amount', 'usd_value']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return the appropriate serializer class."""
        if self.action == 'create':
            return TransactionCreateSerializer
        return TreasuryTransactionSerializer
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute a transaction."""
        transaction = self.get_object()
        
        # Check if user is a guardian
        if not hasattr(request.user, 'guardian'):
            return Response(
                {"detail": "Only guardians can execute transactions."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if transaction is approved
        if transaction.status != TreasuryTransaction.Status.APPROVED:
            return Response(
                {"detail": "This transaction is not approved."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Execute the transaction
        success = transaction.execute()
        
        if success:
            return Response({"status": "transaction executed"})
        else:
            return Response(
                {"detail": "Failed to execute transaction."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a transaction."""
        transaction = self.get_object()
        
        # Check if user is a guardian or the proposer
        is_guardian = hasattr(request.user, 'guardian')
        is_proposer = transaction.proposer == request.user
        
        if not (is_guardian or is_proposer):
            return Response(
                {"detail": "Only guardians or the proposer can cancel transactions."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if transaction can be cancelled
        if transaction.status not in [TreasuryTransaction.Status.PENDING, TreasuryTransaction.Status.APPROVED]:
            return Response(
                {"detail": "This transaction cannot be cancelled in its current state."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cancel the transaction
        transaction.status = TreasuryTransaction.Status.REJECTED
        transaction.save()
        
        return Response({"status": "transaction cancelled"})


class TransactionApprovalViewSet(viewsets.ModelViewSet):
    """
    API endpoint for transaction approvals.
    """
    
    queryset = TransactionApproval.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['transaction', 'guardian', 'approved']
    ordering_fields = ['created_at']
    ordering = ['created_at']
    
    def get_serializer_class(self):
        """Return the appropriate serializer class."""
        if self.action == 'create':
            return TransactionApprovalCreateSerializer
        return TransactionApprovalSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        
        # Staff can see all approvals
        if user.is_staff:
            return TransactionApproval.objects.all()
        
        # Guardians can see their own approvals
        if hasattr(user, 'guardian'):
            return TransactionApproval.objects.filter(guardian__user=user)
        
        # Regular users can see approvals for transactions they proposed
        return TransactionApproval.objects.filter(transaction__proposer=user)
    
    def create(self, request, *args, **kwargs):
        """Create a new approval."""
        # Check if user is a guardian
        if not hasattr(request.user, 'guardian'):
            return Response(
                {"detail": "Only guardians can approve transactions."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)


class TreasuryMetricViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for treasury metrics (read-only).
    """
    
    queryset = TreasuryMetric.objects.all()
    serializer_class = TreasuryMetricSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['timestamp', 'total_value_usd', 'reserve_ratio']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get the latest treasury metric."""
        latest = TreasuryMetric.objects.order_by('-timestamp').first()
        if not latest:
            return Response(
                {"detail": "No treasury metrics available."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(latest)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def historical(self, request):
        """Get historical treasury metrics."""
        # Get time range from query params
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # Get metrics within time range
        metrics = TreasuryMetric.objects.filter(
            timestamp__gte=start_date
        ).order_by('timestamp')
        
        # Group by day if more than 90 days
        if days > 90:
            # Implementation would depend on database, but would aggregate by day
            pass
        
        serializer = self.get_serializer(metrics, many=True)
        return Response(serializer.data)


class AllocationStrategyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for allocation strategies.
    """
    
    queryset = AllocationStrategy.objects.all()
    serializer_class = AllocationStrategySerializer
    permission_classes = [permissions.IsAuthenticated, IsGuardianOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-is_active', 'name']
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate this strategy and deactivate all others."""
        strategy = self.get_object()
        
        # Check if user is a guardian
        if not hasattr(request.user, 'guardian'):
            return Response(
                {"detail": "Only guardians can activate strategies."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Deactivate all other strategies
        AllocationStrategy.objects.exclude(id=strategy.id).update(is_active=False)
        
        # Activate this strategy
        strategy.is_active = True
        strategy.save()
        
        return Response({"status": "strategy activated"})
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get the active allocation strategy."""
        active = AllocationStrategy.objects.filter(is_active=True).first()
        if not active:
            return Response(
                {"detail": "No active allocation strategy."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(active)
        return Response(serializer.data)


class AssetAllocationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for asset allocations.
    """
    
    queryset = AssetAllocation.objects.all()
    serializer_class = AssetAllocationSerializer
    permission_classes = [permissions.IsAuthenticated, IsGuardianOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['strategy', 'asset_type']
    ordering_fields = ['target_percentage']
    ordering = ['-target_percentage']
    
    def get_queryset(self):
        """Filter queryset based on strategy."""
        strategy_id = self.request.query_params.get('strategy_id')
        if strategy_id:
            return AssetAllocation.objects.filter(strategy_id=strategy_id)
        return AssetAllocation.objects.all()

    @action(detail=False, methods=['get'])
    def pending_for_guardian(self, request):
        """Get transactions pending approval for the current guardian."""
        try:
            guardian = Guardian.objects.get(user=request.user, is_active=True)
        except Guardian.DoesNotExist:
            return Response(
                {'detail': 'User is not an active guardian.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get transactions that the guardian hasn't approved yet
        approved_transaction_ids = TransactionApproval.objects.filter(
            guardian=guardian
        ).values_list('transaction_id', flat=True)
        
        pending_transactions = TreasuryTransaction.objects.filter(
            status=TreasuryTransaction.Status.PENDING
        ).exclude(id__in=approved_transaction_ids)
        
        serializer = TreasuryTransactionSerializer(pending_transactions, many=True)
        return Response(serializer.data) 