"""bookings/permissions.py - object-level permission for booking ownership."""
from rest_framework import permissions


class IsBookingOwner(permissions.BasePermission):
    """Only the booking's owner can view or modify it."""

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
