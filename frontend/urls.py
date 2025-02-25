"""
URL patterns for the frontend app.
"""

from django.urls import path
from django.views.generic import TemplateView

urlpatterns = [
    # Serve the main index.html for all non-matching routes
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
] 