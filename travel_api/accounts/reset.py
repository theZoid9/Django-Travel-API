from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.db import transaction
from rest_framework import generics, serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

class ResetThrottle(AnonRateThrottle):
    rate = '5/hour'

class ResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField(max_length=128)
    token = serializers.CharField(max_length=128)
    new_password = serializers.CharField(write_only=True)
    new_password_confirm = serializers.CharField(write_only=True)

class PasswordResetRequestView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ResetThrottle]
    serializer_class = ResetRequestSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for user in get_user_model().objects.filter(email__iexact=serializer.validated_data['email'], is_active=True):
            if user.has_usable_password():
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                send_mail('Reset your travel API password',
                          f'Submit uid: {uid} and token: {token} with new_password and new_password_confirm to /api/v1/accounts/password/reset/confirm/.',
                          settings.DEFAULT_FROM_EMAIL, [user.email])
        return Response({'detail': 'If an eligible account exists, password reset instructions have been sent.'})

class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ResetThrottle]
    serializer_class = ResetConfirmSerializer
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            try:
                pk = force_str(urlsafe_base64_decode(data['uid']))
                user = get_user_model().objects.select_for_update().get(pk=pk, is_active=True)
            except (ValueError, TypeError, OverflowError, UnicodeDecodeError, get_user_model().DoesNotExist):
                raise serializers.ValidationError({'token': 'Invalid or expired reset token.'})
            if not default_token_generator.check_token(user, data['token']):
                raise serializers.ValidationError({'token': 'Invalid or expired reset token.'})
            if data['new_password'] != data['new_password_confirm']:
                raise serializers.ValidationError({'new_password_confirm': 'Passwords must match.'})
            try:
                validate_password(data['new_password'], user)
            except DjangoValidationError as exc:
                raise serializers.ValidationError({'new_password': exc.messages})
            user.set_password(data['new_password'])
            user.save(update_fields=['password'])
        return Response({'detail': 'Password reset successfully.'})
