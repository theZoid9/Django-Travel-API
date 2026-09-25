"""
itineraries/permissions.py

Custom object-level permission classes for trips: ownership,
owner-or-collaborator read access, and role-based edit access.
"""
from rest_framework import permissions


class IsTripOwner(permissions.BasePermission):
    """Only the trip owner may perform the action."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


class IsTripOwnerOrCollaborator(permissions.BasePermission):
    """
    Owners and collaborators may safely read a trip; only the owner may
    perform unsafe (write) methods.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.owner == request.user or request.user in obj.collaborators.all()
        return obj.owner == request.user


class CanEditItinerary(permissions.BasePermission):
    """
    Role-based edit permission: the owner can always edit; collaborators
    can edit only if their role is 'editor' or 'admin'.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.owner == request.user or request.user in obj.collaborators.all()
        if obj.owner == request.user:
            return True
        collaboration = obj.collaborations.filter(user=request.user).first()
        return bool(collaboration and collaboration.role in ['editor', 'admin'])
