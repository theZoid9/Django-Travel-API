from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('profile/', views.UserProfileDetailView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change_password'),
    path('me/', views.UserMeView.as_view(), name='me'),
]
