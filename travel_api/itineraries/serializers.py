from rest_framework import serializers
from django.utils import timezone
from .models import Itinerary, TripCollaborator, DailyPlan, DayActivity, ActivityLog

class TripCollaboratorSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    class Meta:
        model = TripCollaborator
        fields = ['id', 'user', 'username', 'role', 'invited_at', 'accepted_at']
        read_only_fields = ['id', 'invited_at']

class DayActivitySerializer(serializers.ModelSerializer):
    activity_name = serializers.CharField(source='activity.name', read_only=True)
    class Meta:
        model = DayActivity
        fields = ['id', 'activity', 'activity_name', 'start_time', 'end_time', 'notes', 'order']
        read_only_fields = ['id']

class DailyPlanSerializer(serializers.ModelSerializer):
    day_activities = DayActivitySerializer(many=True, read_only=True)
    activity_count = serializers.SerializerMethodField(help_text='Activity count')
    class Meta:
        model = DailyPlan
        fields = ['id', 'day_number', 'date', 'title', 'notes', 'day_activities', 'activity_count']
        read_only_fields = ['id']
    def get_activity_count(self, obj): return obj.day_activities.count()

class ActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='System')
    class Meta:
        model = ActivityLog
        fields = ['id', 'user', 'username', 'action', 'details', 'created_at']
        read_only_fields = ['id', 'created_at']

class BaseItinerarySerializer(serializers.ModelSerializer):
    total_days = serializers.SerializerMethodField(help_text='Total days')
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    class Meta:
        model = Itinerary
        fields = ['id', 'title', 'status', 'status_display', 'start_date', 'end_date', 'total_days']
        read_only_fields = ['id']
    def get_total_days(self, obj): return obj.calculate_total_days()

class ItineraryListSerializer(BaseItinerarySerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    collaborator_count = serializers.SerializerMethodField(help_text='Collaborator count')
    class Meta(BaseItinerarySerializer.Meta):
        fields = BaseItinerarySerializer.Meta.fields + ['owner_username', 'budget_estimate', 'collaborator_count', 'cover_image', 'created_at']
        read_only_fields = ['id', 'created_at']
    def get_collaborator_count(self, obj): return obj.collaborators.count()

class ItineraryDetailSerializer(BaseItinerarySerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    daily_plans = DailyPlanSerializer(many=True, read_only=True)
    collaborators = TripCollaboratorSerializer(many=True, read_only=True)
    total_cost = serializers.SerializerMethodField(help_text='Total cost')
    class Meta(BaseItinerarySerializer.Meta):
        fields = BaseItinerarySerializer.Meta.fields + ['owner', 'owner_username', 'description', 'budget_estimate', 'daily_plans', 'collaborators', 'cover_image', 'total_cost', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    def get_total_cost(self, obj): return float(obj.calculate_total_cost())
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if self.context.get('include_logs', False):
            rep['recent_logs'] = ActivityLogSerializer(instance.activity_logs.all()[:20], many=True).data
        return rep

class ItineraryCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Itinerary
        fields = ['title', 'description', 'start_date', 'end_date', 'status', 'budget_estimate', 'cover_image']
    def validate(self, attrs):
        if attrs.get('start_date') and attrs.get('end_date') and attrs['end_date'] < attrs['start_date']:
            raise serializers.ValidationError({'end_date': 'End date must be >= start date.'})
        return attrs
    def create(self, validated_data):
        user = self.context['request'].user
        itin = Itinerary.objects.create(owner=user, **validated_data)
        TripCollaborator.objects.create(itinerary=itin, user=user, role='owner', accepted_at=timezone.now())
        return itin

class AddCollaboratorSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(help_text='User ID')
    role = serializers.ChoiceField(choices=['collaborator', 'viewer'], help_text='Role')
    def validate_user_id(self, value):
        from django.contrib.auth import get_user_model
        if not get_user_model().objects.filter(pk=value).exists():
            raise serializers.ValidationError('User does not exist.')
        return value
