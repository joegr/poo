"""
URL patterns for the governance app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'proposals', views.ProposalViewSet)
router.register(r'votes', views.VoteViewSet)
router.register(r'comments', views.ProposalCommentViewSet)
router.register(r'tokens', views.GovernanceTokenViewSet)
router.register(r'guardians', views.GuardianViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 