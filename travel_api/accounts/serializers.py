"""
accounts/serializers.py

Serializers covering registration, login, profile retrieval/update,
password change and password reset flows.
"""
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Base read/update serializer for the profile endpoints."""
    full_name = serializers.ReadOnlyField()
    total_trips = serializers.SerializerMethodField(help_text='Number of trips this user owns.')

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'date_of_birth', 'bio', 'profile_picture',
            'travel_preferences', 'total_trips', 'created_at',
        ]
        read_only_fields = ['id', 'username', 'created_at']

    def get_total_trips(self, obj):
        return obj.total_trips()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for new-account creation. Demonstrates write-only fields for
    sensitive data (password) and a custom create() override.
    """
    password = serializers.CharField(
        write_only=True, min_length=8, help_text='At least 8 characters.'
    )
    password_confirm = serializers.CharField(write_only=True, help_text='Repeat the password.')

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
        read_only_fields = ['id']

    def validate_email(self, value):
        """Field-level validation: ensure the email isn't already registered."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value

    def validate(self, data):
        """Object-level validation: passwords must match and pass Django's validators."""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        try:
            password_validation.validate_password(data['password'])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return data

    def create(self, validated_data):
        """Create the user with a properly hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer validating login credentials (not tied to a model)."""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for authenticated password-change requests."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for requesting a password reset email/token."""
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a password reset with uid/token."""
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_new_password(self, value):
        try:
            password_validation.validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages))
        return value
