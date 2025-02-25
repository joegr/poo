"""
URL patterns for the analytics app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Create a router and register our viewsets with it.
router = DefaultRouter()
# Add viewsets here when they are created
# router.register(r'metrics', views.MetricsViewSet)

urlpatterns = [
    path('', include(router.urls)),
] 