from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import TripCollaborator

class IsTripOwner(BasePermission):
    message = 'Only the trip owner can perform this action.'
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user

class IsTripOwnerOrCollaborator(BasePermission):
    message = 'You do not have permission for this action.'
    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user: return True
        try:
            c = TripCollaborator.objects.get(itinerary=obj, user=request.user)
        except TripCollaborator.DoesNotExist:
            return False
        if request.method in SAFE_METHODS: return True
        return c.role in ('owner', 'collaborator')

class IsTripParticipant(BasePermission):
    message = 'You are not a participant on this trip.'
    def has_object_permission(self, request, view, obj):
        if obj.owner == request.user: return True
        return TripCollaborator.objects.filter(itinerary=obj, user=request.user).exists()
