from travel_api.access import OwnedItineraryMixin
from rest_framework import serializers
from .models import Accommodation, Activity, AccommodationBooking, ActivityBooking

class AccommodationListSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    type_display = serializers.CharField(source='get_accommodation_type_display', read_only=True)
    class Meta:
        model = Accommodation
        fields = ['id', 'name', 'destination_name', 'type_display', 'price_per_night', 'rating', 'is_available', 'image']
        read_only_fields = ['id']

class AccommodationDetailSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    type_display = serializers.CharField(source='get_accommodation_type_display', read_only=True)
    class Meta:
        model = Accommodation
        fields = ['id', 'name', 'destination', 'destination_name', 'accommodation_type', 'type_display', 'price_per_night', 'address', 'amenities', 'rating', 'image', 'is_available', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class ActivityListSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    duration = serializers.SerializerMethodField(help_text='Duration display')
    class Meta:
        model = Activity
        fields = ['id', 'name', 'destination_name', 'type_display', 'price', 'duration', 'rating', 'is_available', 'image']
        read_only_fields = ['id']
    def get_duration(self, obj):
        return obj.duration_display()

class ActivityDetailSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    duration = serializers.SerializerMethodField(help_text='Duration display')
    is_bookable = serializers.SerializerMethodField(help_text='Can be booked')
    class Meta:
        model = Activity
        fields = ['id', 'name', 'destination', 'destination_name', 'activity_type', 'type_display', 'price', 'duration_minutes', 'duration', 'description', 'rating', 'image', 'is_available', 'max_participants', 'is_bookable', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    def get_duration(self, obj): return obj.duration_display()
    def get_is_bookable(self, obj): return obj.is_available

class AccommodationBookingSerializer(OwnedItineraryMixin, serializers.ModelSerializer):
    accommodation_name = serializers.CharField(source='accommodation.name', read_only=True, default='')
    class Meta:
        model = AccommodationBooking
        fields = ['id', 'itinerary', 'accommodation', 'accommodation_name', 'check_in', 'check_out', 'guests_count', 'total_price', 'status', 'special_requests', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']
    def validate(self, attrs):
        check_in = attrs.get('check_in', getattr(self.instance, 'check_in', None))
        check_out = attrs.get('check_out', getattr(self.instance, 'check_out', None))
        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError({'check_out': 'Check-out must be after check-in.'})
        return attrs
    def update(self, instance, validated_data):
        from django.db import transaction
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            instance.total_price = instance.calculate_total_price()
            instance.save(update_fields=['total_price'])
        return instance
    def create(self, validated_data):
        b = super().create(validated_data)
        b.total_price = b.calculate_total_price()
        b.save(update_fields=['total_price'])
        return b

class ActivityBookingSerializer(OwnedItineraryMixin, serializers.ModelSerializer):
    activity_name = serializers.CharField(source='activity.name', read_only=True, default='')
    class Meta:
        model = ActivityBooking
        fields = ['id', 'itinerary', 'activity', 'activity_name', 'date', 'participants_count', 'total_price', 'status', 'special_requests', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_price', 'created_at', 'updated_at']
    def validate(self, attrs):
        act = attrs.get('activity', getattr(self.instance, 'activity', None))
        p = attrs.get('participants_count', getattr(self.instance, 'participants_count', 1))
        if act and p > act.max_participants:
            raise serializers.ValidationError({'participants_count': f'Max is {act.max_participants}.'})
        return attrs
    def update(self, instance, validated_data):
        from django.db import transaction
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            instance.total_price = instance.calculate_total_price()
            instance.save(update_fields=['total_price'])
        return instance
    def create(self, validated_data):
        b = super().create(validated_data)
        b.total_price = b.calculate_total_price()
        b.save(update_fields=['total_price'])
        return b
