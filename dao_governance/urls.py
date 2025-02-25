"""
URL Configuration for dao_governance project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

# API documentation schema
schema_view = get_schema_view(
    openapi.Info(
        title="DAO Governance API",
        default_version='v1',
        description="API for DAO Governance System",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    
    # REST API endpoints
    path('api/v1/governance/', include('governance.urls')),
    path('api/v1/treasury/', include('treasury.urls')),
    path('api/v1/identity/', include('identity.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
    
    # GraphQL endpoint
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True))),
    
    # Authentication
    path('api/v1/auth/', include('rest_framework.urls')),
    
    # Health checks
    path('health/', include('health_check.urls')),
    
    # Prometheus metrics
    path('', include('django_prometheus.urls')),
    
    # Frontend (serve the index.html for all non-matching routes)
    path('', include('frontend.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 