"""
accounts/permissions.py

Custom permission classes shared across the accounts app.
"""
from rest_framework import permissions


class IsSelf(permissions.BasePermission):
    """Only allow a user to view/edit their own account object."""

    def has_object_permission(self, request, view, obj):
        return obj == request.user
