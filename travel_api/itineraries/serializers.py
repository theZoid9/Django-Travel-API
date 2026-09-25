"""
itineraries/serializers.py

Serializer inheritance and per-operation serializers for Itinerary, plus
nested Collaboration/DailyPlan serializers.
"""
from rest_framework import serializers

from destinations.models import Destination
from destinations.serializers import DestinationListSerializer

from .models import Collaboration, DailyPlan, Itinerary


class CollaborationSerializer(serializers.ModelSerializer):
    """Serializer for the Itinerary<->User through model."""

    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Collaboration
        fields = ['id', 'user', 'username', 'email', 'role', 'invited_at']
        read_only_fields = ['id', 'invited_at']


class DailyPlanSerializer(serializers.ModelSerializer):
    """Daily plan serializer with a computed activities_count field."""

    activities_count = serializers.SerializerMethodField()

    class Meta:
        model = DailyPlan
        fields = ['id', 'day_number', 'date', 'title', 'notes', 'activities', 'activities_count']

    def get_activities_count(self, obj):
        return obj.activities.count()

    def validate(self, data):
        """Object-level validation delegating to the model's clean()."""
        instance = DailyPlan(**{k: v for k, v in data.items() if k != 'activities'})
        instance.itinerary = data.get('itinerary') or getattr(self.instance, 'itinerary', None)
        try:
            instance.clean()
        except Exception as exc:  # noqa: BLE001 - surface as DRF validation error
            raise serializers.ValidationError(str(exc))
        return data


class BaseItinerarySerializer(serializers.ModelSerializer):
    """
    Base serializer defining shared computed fields, extended by the
    list/detail serializers below (serializer inheritance).
    """
    duration_days = serializers.ReadOnlyField()
    budget_remaining = serializers.ReadOnlyField()

    class Meta:
        model = Itinerary
        fields = '__all__'
        read_only_fields = ['id', 'owner', 'created_at', 'updated_at']


class ItineraryListSerializer(BaseItinerarySerializer):
    """Lightweight list serializer (extends BaseItinerarySerializer)."""

    destination_name = serializers.CharField(source='destination.name', read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta(BaseItinerarySerializer.Meta):
        fields = [
            'id', 'title', 'destination', 'destination_name', 'owner', 'owner_username',
            'start_date', 'end_date', 'duration_days', 'budget', 'budget_remaining',
            'status', 'is_public',
        ]


class ItineraryDetailSerializer(BaseItinerarySerializer):
    """Detailed serializer with nested objects (extends BaseItinerarySerializer)."""

    destination = DestinationListSerializer(read_only=True)
    destination_id = serializers.PrimaryKeyRelatedField(
        queryset=Destination.objects.all(), source='destination', write_only=True,
    )
    daily_plans = DailyPlanSerializer(many=True, read_only=True)
    collaborations = CollaborationSerializer(many=True, read_only=True)
    bookings_count = serializers.SerializerMethodField()

    def get_bookings_count(self, obj):
        return obj.bookings.count()

    def validate(self, data):
        """Custom validation for dates and budget."""
        start = data.get('start_date', getattr(self.instance, 'start_date', None))
        end = data.get('end_date', getattr(self.instance, 'end_date', None))
        if start and end and end < start:
            raise serializers.ValidationError({'end_date': 'End date must be after start date'})
        if data.get('budget') is not None and data['budget'] < 0:
            raise serializers.ValidationError({'budget': 'Budget must be positive'})
        return data

    def create(self, validated_data):
        """Create itinerary and auto-create a linked Budget record."""
        itinerary = Itinerary.objects.create(**validated_data)
        from budgets.models import Budget
        Budget.objects.create(itinerary=itinerary)
        return itinerary

    def update(self, instance, validated_data):
        """Explicit update override so status transitions can be logged later if needed."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.full_clean(exclude=['collaborators'])
        instance.save()
        return instance


class ItineraryCreateUpdateSerializer(serializers.ModelSerializer):
    """Separate, minimal serializer used specifically for create/update operations."""

    class Meta:
        model = Itinerary
        fields = ['title', 'description', 'destination', 'start_date', 'end_date', 'budget', 'is_public']

    def validate_budget(self, value):
        if value <= 0:
            raise serializers.ValidationError('Budget must be greater than zero')
        return value
