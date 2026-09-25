"""
bookings/serializers.py

Serializers for Accommodation, Activity and Booking (list/detail split
for bookings, plus nested read-only summaries of the booked item).
"""
from rest_framework import serializers

from .models import Accommodation, Activity, Booking


class AccommodationSerializer(serializers.ModelSerializer):
    """Full serializer for accommodations."""

    class Meta:
        model = Accommodation
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def validate_price_per_night(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price per night must be greater than zero.')
        return value


class ActivitySerializer(serializers.ModelSerializer):
    """Full serializer for activities."""

    is_full_day = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = '__all__'
        read_only_fields = ['id', 'created_at']

    def get_is_full_day(self, obj):
        return obj.is_full_day()

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError('Price cannot be negative.')
        return value


class BookingListSerializer(serializers.ModelSerializer):
    """Lightweight list serializer for bookings."""

    item_name = serializers.SerializerMethodField()
    itinerary_title = serializers.CharField(source='itinerary.title', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'itinerary', 'itinerary_title', 'item_name', 'booking_date',
            'price', 'status', 'confirmation_code',
        ]

    def get_item_name(self, obj):
        if obj.accommodation:
            return obj.accommodation.name
        if obj.activity:
            return obj.activity.name
        return None


class BookingDetailSerializer(serializers.ModelSerializer):
    """Detailed booking serializer with nested accommodation/activity summaries."""

    accommodation_detail = AccommodationSerializer(source='accommodation', read_only=True)
    activity_detail = ActivitySerializer(source='activity', read_only=True)
    refund_amount = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 'confirmation_code']

    def get_refund_amount(self, obj):
        return obj.calculate_refund()

    def validate(self, data):
        """Object-level validation mirroring the model's clean() rule."""
        accommodation = data.get('accommodation', getattr(self.instance, 'accommodation', None))
        activity = data.get('activity', getattr(self.instance, 'activity', None))
        if not accommodation and not activity:
            raise serializers.ValidationError('Booking must have either accommodation or activity.')
        if accommodation and activity:
            raise serializers.ValidationError('Booking cannot have both accommodation and activity.')
        return data

    def create(self, validated_data):
        """Auto-assign the requesting user and generate a confirmation code."""
        request = self.context.get('request')
        booking = Booking(**validated_data)
        if request:
            booking.user = request.user
        booking.generate_confirmation_code()
        booking.full_clean()
        booking.save()
        return booking


class BookingSerializer(BookingDetailSerializer):
    """Alias serializer used for create operations via the ViewSet (serializer inheritance)."""
    pass
