from rest_framework import serializers
from .models import Category, Tag, Destination, DestinationPhoto

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['id', 'slug']

class CategorySerializer(serializers.ModelSerializer):
    destination_count = serializers.SerializerMethodField(help_text='Number of destinations')
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'destination_count']
        read_only_fields = ['id', 'slug']
    def get_destination_count(self, obj):
        return obj.destinations.count()

class DestinationPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationPhoto
        fields = ['id', 'image', 'caption', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

class DestinationListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True, default=None)
    rating_display = serializers.SerializerMethodField(help_text='Rating display')
    class Meta:
        model = Destination
        fields = ['id', 'name', 'slug', 'country', 'city', 'category_name', 'image', 'is_featured', 'avg_rating', 'rating_display']
        read_only_fields = ['id', 'slug', 'avg_rating']
    def get_rating_display(self, obj):
        return 'Not rated' if obj.avg_rating == 0 else f'{obj.avg_rating:.1f} / 5.0'

class DestinationDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    photos = DestinationPhotoSerializer(many=True, read_only=True)
    top_activities = serializers.SerializerMethodField(help_text='Top activities')
    review_count = serializers.SerializerMethodField(help_text='Review count')
    class Meta:
        model = Destination
        fields = ['id', 'name', 'slug', 'country', 'city', 'region', 'description', 'latitude', 'longitude', 'category', 'tags', 'photos', 'image', 'is_featured', 'avg_rating', 'top_activities', 'review_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'slug', 'avg_rating', 'created_at', 'updated_at']
    def get_top_activities(self, obj):
        from bookings.serializers import ActivityListSerializer
        return ActivityListSerializer(obj.get_top_activities(), many=True).data
    def get_review_count(self, obj):
        return obj.reviews.count()
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if self.context.get('include_weather', False):
            rep['weather_info'] = 'Weather data not yet integrated'
        return rep

class DestinationCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = ['name', 'country', 'city', 'region', 'description', 'latitude', 'longitude', 'category', 'tags', 'image', 'is_featured']
    def validate_country(self, value):
        if not value.strip():
            raise serializers.ValidationError('Country cannot be empty.')
        return value.strip()
