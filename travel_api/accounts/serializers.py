from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class BaseUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField(help_text='Best available display name')
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'full_name']
    def get_full_name(self, obj):
        return obj.get_full_display_name()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, help_text='Password (min 8 chars)')
    password_confirm = serializers.CharField(write_only=True, help_text='Confirm password')
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password_confirm', 'phone', 'travel_style']
        read_only_fields = ['id']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

class UserSerializer(BaseUserSerializer):
    travel_style = serializers.CharField(source='get_travel_style_display', read_only=True)
    class Meta(BaseUserSerializer.Meta):
        fields = ['id', 'username', 'email', 'full_name', 'phone', 'travel_style', 'avatar', 'date_of_birth']
        read_only_fields = ['id', 'username']

class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    favorite_count = serializers.SerializerMethodField(help_text='Number of favorite destinations')
    class Meta:
        model = UserProfile
        fields = ['id', 'username', 'bio', 'preferred_currency', 'home_country', 'favorite_count']
        read_only_fields = ['id', 'username']

    def get_favorite_count(self, obj):
        return obj.favorite_count()

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if self.context.get('include_favorites', False):
            rep['favorite_destinations'] = list(instance.favorite_destinations.values_list('id', flat=True))
        return rep

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, help_text='Current password')
    new_password = serializers.CharField(write_only=True, min_length=8, help_text='New password')
    new_password_confirm = serializers.CharField(write_only=True, help_text='Confirm new password')

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs.pop('new_password_confirm'):
            raise serializers.ValidationError({'new_password': 'Passwords do not match.'})
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
