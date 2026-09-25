"""reviews/permissions.py - object-level ownership permission for reviews."""
from rest_framework import permissions


class IsReviewOwner(permissions.BasePermission):
    """Only the review's author can edit or delete it; anyone can read."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user
