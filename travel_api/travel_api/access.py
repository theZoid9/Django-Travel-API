from rest_framework import serializers
from rest_framework.permissions import BasePermission, SAFE_METHODS

class OwnedItineraryMixin:
    def validate_itinerary(self, value):
        if value.owner_id != self.context['request'].user.pk:
            raise serializers.ValidationError('Choose an itinerary you own.')
        return value

class IsReviewAuthorOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.user_id == request.user.pk
