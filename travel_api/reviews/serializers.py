from rest_framework import serializers
from .models import Review, ActivityReview

class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(help_text='Author name')
    destination_name = serializers.CharField(source='destination.name', read_only=True)
    class Meta:
        model = Review
        fields = ['id', 'user', 'username', 'destination', 'destination_name', 'rating', 'title', 'comment', 'is_anonymous', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    def get_username(self, obj):
        return 'Anonymous' if obj.is_anonymous else obj.user.username
    def validate_rating(self, value):
        if not (1 <= value <= 5): raise serializers.ValidationError('Rating 1-5.')
        return value
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

class ActivityReviewSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField(help_text='Author name')
    activity_name = serializers.CharField(source='activity.name', read_only=True)
    class Meta:
        model = ActivityReview
        fields = ['id', 'user', 'username', 'activity', 'activity_name', 'rating', 'title', 'comment', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    def get_username(self, obj): return obj.user.username
    def validate_rating(self, value):
        if not (1 <= value <= 5): raise serializers.ValidationError('Rating 1-5.')
        return value
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
