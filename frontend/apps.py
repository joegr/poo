"""
Frontend app configuration.
"""

from django.apps import AppConfig


class FrontendConfig(AppConfig):
    """Frontend app configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'frontend' 