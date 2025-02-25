"""
Custom permissions for the governance app.
"""

from rest_framework import permissions


class IsProposalOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of a proposal to edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.proposer == request.user


class IsVoteOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of a vote to edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.voter == request.user


class IsCommentOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of a comment to edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.author == request.user


class IsTokenOwnerOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow owners of a token to edit it."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.holder == request.user


class IsGuardianOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow guardians to edit their own data."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the guardian or admins
        return obj.user == request.user or request.user.is_staff


class IsMemberOrReadOnly(permissions.BasePermission):
    """Custom permission to only allow members to edit their own data."""
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the member or admins
        return obj.user == request.user or request.user.is_staff 