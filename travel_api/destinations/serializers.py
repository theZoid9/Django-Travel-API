"""
destinations/serializers.py

List/detail serializer split, with SerializerMethodFields for computed
review/itinerary counts and nested top-activities.
"""
from rest_framework import serializers

from .models import Destination


class DestinationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer used for the browsable destination list."""

    average_rating = serializers.ReadOnlyField(help_text='Mean review rating (0-5).')
    review_count = serializers.SerializerMethodField(help_text='Number of reviews submitted.')
    budget_tier = serializers.SerializerMethodField(help_text='budget / moderate / luxury.')

    class Meta:
        model = Destination
        fields = [
            'id', 'name', 'slug', 'country', 'category', 'climate',
            'avg_daily_cost', 'image', 'average_rating', 'review_count', 'budget_tier',
        ]
        read_only_fields = ['id', 'slug']

    def get_review_count(self, obj):
        return obj.reviews.count()

    def get_budget_tier(self, obj):
        return obj.budget_tier()


class DestinationDetailSerializer(serializers.ModelSerializer):
    """Full serializer for the destination detail page, with nested extras."""

    average_rating = serializers.ReadOnlyField()
    total_itineraries = serializers.SerializerMethodField()
    top_activities = serializers.SerializerMethodField()
    accommodation_count = serializers.SerializerMethodField()

    class Meta:
        model = Destination
        fields = '__all__'
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']

    def get_total_itineraries(self, obj):
        return obj.itineraries.count()

    def get_accommodation_count(self, obj):
        return obj.accommodations.count()

    def get_top_activities(self, obj):
        """Nested serializer usage: top 5 activities for this destination."""
        from bookings.serializers import ActivitySerializer
        activities = obj.activities.filter(is_available=True)[:5]
        return ActivitySerializer(activities, many=True, context=self.context).data

    def to_representation(self, instance):
        """Override to_representation to drop lat/long when not set, keeping payloads tidy."""
        data = super().to_representation(instance)
        if data.get('latitude') is None:
            data.pop('latitude', None)
            data.pop('longitude', None)
        return data


class DestinationCreateUpdateSerializer(serializers.ModelSerializer):
    """Separate serializer used for create/update (admin) operations."""

    class Meta:
        model = Destination
        fields = [
            'name', 'country', 'description', 'category', 'climate',
            'best_time_to_visit', 'avg_daily_cost', 'image',
            'latitude', 'longitude', 'is_active',
        ]

    def validate_avg_daily_cost(self, value):
        """Field-level validation."""
        if value <= 0:
            raise serializers.ValidationError('Average daily cost must be greater than zero.')
        return value

    def validate(self, data):
        """Object-level validation mirroring the model's clean() method."""
        lat = data.get('latitude')
        lon = data.get('longitude')
        if (lat is None) != (lon is None):
            raise serializers.ValidationError('Both latitude and longitude must be provided together, or neither.')
        return data
