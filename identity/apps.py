"""
Identity app configuration.
"""

from django.apps import AppConfig


class IdentityConfig(AppConfig):
    """Identity app configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'identity' 