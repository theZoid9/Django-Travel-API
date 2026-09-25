"""
accounts/views.py

Authentication & profile endpoints:
- register (FBV, POST)
- login (FBV, POST)
- password_change (FBV, POST)
- password_reset_request / password_reset_confirm (FBVs, POST)
- UserProfileView (CBV, GET/PUT/PATCH)
"""
from django.contrib.auth import authenticate, get_user_model
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import (
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    UserRegistrationSerializer,
    UserSerializer,
)

User = get_user_model()


def _tokens_for_user(user):
    """Business-logic helper: issue a fresh JWT access/refresh pair."""
    refresh = RefreshToken.for_user(user)
    return {'refresh': str(refresh), 'access': str(refresh.access_token)}


@extend_schema(
    request=UserRegistrationSerializer,
    responses={201: UserSerializer},
    examples=[OpenApiExample(
        'Register example',
        value={'username': 'jane', 'email': 'jane@example.com', 'password': 'Str0ngPass!', 'password_confirm': 'Str0ngPass!'},
    )],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user account and immediately return JWT tokens so the
    client can log the user in without a second request.
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'user': UserSerializer(user).data,
            'tokens': _tokens_for_user(user),
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=LoginSerializer,
    responses={200: UserSerializer},
    examples=[OpenApiExample('Login example', value={'username': 'jane', 'password': 'Str0ngPass!'})],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Authenticate a user with username/password and return JWT tokens."""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password'],
        )
        if user is not None:
            return Response({
                'user': UserSerializer(user).data,
                'tokens': _tokens_for_user(user),
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def password_change(request):
    """Change the password of the currently authenticated user."""
    serializer = PasswordChangeSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'old_password': 'Incorrect password.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password changed successfully.'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Step 1 of the reset flow: generate a uid/token pair for the given email.
    In production this would be emailed to the user; here it is returned in
    the response so the flow can be exercised end-to-end without an SMTP
    backend configured.
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = User.objects.get(email__iexact=serializer.validated_data['email'])
        except User.DoesNotExist:
            # Do not reveal whether the email exists.
            return Response({'detail': 'If that email exists, a reset link has been generated.'})
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        return Response({'detail': 'Reset token generated.', 'uid': uid, 'token': token})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """Step 2 of the reset flow: verify the uid/token and set a new password."""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data['uid']))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, serializer.validated_data['token']):
            return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'detail': 'Password reset successful.'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update the authenticated user's own profile.

    GET returns the current profile; PUT/PATCH update it. Only the
    request's own user object is ever accessible here.
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
