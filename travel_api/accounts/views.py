from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from .models import UserProfile
from .serializers import UserRegistrationSerializer, UserSerializer, UserProfileSerializer, ChangePasswordSerializer
from .permissions import IsProfileOwner

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        output = UserSerializer(user)
        return Response(output.data, status=status.HTTP_201_CREATED)

class UserProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, IsProfileOwner]

    def get_object(self):
        return self.request.user.profile

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['include_favorites'] = True
        return context

class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'detail': 'Password changed successfully.'}, status=status.HTTP_200_OK)

class UserMeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
