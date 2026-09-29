from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwner(BasePermission):
    message = 'You must be the owner of this object.'
    def has_object_permission(self, request, view, obj):
        return getattr(obj, 'owner', None) == request.user

class IsOwnerOrReadOnly(BasePermission):
    message = 'You must be the owner to modify this object.'
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, 'owner', None) == request.user

class IsCollaborator(BasePermission):
    message = 'You must be a collaborator on this trip.'
    def has_object_permission(self, request, view, obj):
        itinerary = getattr(obj, 'itinerary', obj)
        return itinerary.collaborators.filter(
            user=request.user, role__in=['owner', 'collaborator']
        ).exists()

class IsOwnerOrCollaborator(BasePermission):
    message = 'You do not have permission to modify this trip.'
    def has_object_permission(self, request, view, obj):
        itinerary = getattr(obj, 'itinerary', obj)
        if request.method in SAFE_METHODS:
            return itinerary.collaborators.filter(user=request.user).exists()
        return itinerary.collaborators.filter(
            user=request.user, role__in=['owner', 'collaborator']
        ).exists()

class IsProfileOwner(BasePermission):
    message = 'You can only access your own profile.'
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user
