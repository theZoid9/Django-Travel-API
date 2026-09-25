"""budgets/permissions.py - restrict budget/expense access to the trip owner or its collaborators."""
from rest_framework import permissions


class IsItineraryOwnerOrCollaborator(permissions.BasePermission):
    """Allow access to the budget/expense if the user owns or collaborates on the parent trip."""

    def has_object_permission(self, request, view, obj):
        itinerary = getattr(obj, 'itinerary', obj)
        return itinerary.owner == request.user or request.user in itinerary.collaborators.all()
