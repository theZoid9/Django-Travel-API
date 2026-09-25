"""accounts/urls.py - authentication & profile endpoints."""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('password/change/', views.password_change, name='password-change'),
    path('password/reset/', views.password_reset_request, name='password-reset-request'),
    path('password/reset/confirm/', views.password_reset_confirm, name='password-reset-confirm'),
]
