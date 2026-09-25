"""reviews/serializers.py"""
from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Full serializer for reviews, with the author's username surfaced read-only."""

    username = serializers.CharField(source='user.username', read_only=True)
    target_name = serializers.ReadOnlyField()

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ['id', 'user', 'helpful_count', 'created_at', 'updated_at']

    def validate(self, data):
        """Object-level validation mirroring the model's clean() rule."""
        destination = data.get('destination', getattr(self.instance, 'destination', None))
        accommodation = data.get('accommodation', getattr(self.instance, 'accommodation', None))
        activity = data.get('activity', getattr(self.instance, 'activity', None))
        targets = [destination, accommodation, activity]
        if sum(1 for t in targets if t) != 1:
            raise serializers.ValidationError('Review must be for exactly one item.')
        return data

    def validate_rating(self, value):
        """Field-level validation."""
        if not (1 <= value <= 5):
            raise serializers.ValidationError('Rating must be between 1 and 5.')
        return value

    def create(self, validated_data):
        """Attach the requesting user automatically."""
        request = self.context.get('request')
        validated_data['user'] = request.user
        return super().create(validated_data)
