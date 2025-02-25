"""
Treasury app configuration.
"""

from django.apps import AppConfig


class TreasuryConfig(AppConfig):
    """Treasury app configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'treasury' 