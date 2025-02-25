"""
URL patterns for the treasury app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'assets', views.AssetViewSet)
router.register(r'balances', views.AssetBalanceViewSet)
router.register(r'transactions', views.TreasuryTransactionViewSet)
router.register(r'approvals', views.TransactionApprovalViewSet)
router.register(r'metrics', views.TreasuryMetricViewSet)
router.register(r'strategies', views.AllocationStrategyViewSet)
router.register(r'allocations', views.AssetAllocationViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 