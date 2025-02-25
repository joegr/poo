"""
URL patterns for the governance app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'proposals', views.ProposalViewSet)
router.register(r'votes', views.VoteViewSet)
router.register(r'comments', views.ProposalCommentViewSet)
router.register(r'tokens', views.GovernanceTokenViewSet)
router.register(r'guardians', views.GuardianViewSet)
router.register(r'members', views.MemberViewSet)
router.register(r'verification-requests', views.VerificationRequestViewSet)
router.register(r'circuit-breakers', views.CircuitBreakerViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 