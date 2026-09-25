"""
Main URL configuration for the Travel Itinerary Planning & Booking API.

All API routes are versioned under /api/v1/. ViewSets are wired up via a
DefaultRouter here (imported from each app's viewsets), while function-based
and class-based views live under each app's own urls.py, included with a
namespace.
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.routers import DefaultRouter

from itineraries.viewsets import ItineraryViewSet, TripAnalyticsViewSet
from destinations.viewsets import DestinationViewSet
from bookings.viewsets import BookingViewSet, AccommodationViewSet, ActivityViewSet
from reviews.viewsets import ReviewViewSet


class OpenRootRouter(DefaultRouter):
    """
    A DefaultRouter whose auto-generated API root view (the directory
    listing at /api/v1/) is publicly readable even though every other
    view in the project defaults to IsAuthenticated. This only affects
    that one listing view - every registered viewset still enforces its
    own get_permissions()/permission_classes normally.
    """
    def get_api_root_view(self, api_urls=None):
        view = super().get_api_root_view(api_urls)
        view.cls.permission_classes = [permissions.AllowAny]
        return view


router = OpenRootRouter()
router.register(r'itineraries', ItineraryViewSet, basename='itinerary')
router.register(r'destinations', DestinationViewSet, basename='destination')
router.register(r'accommodations', AccommodationViewSet, basename='accommodation')
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'analytics', TripAnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('admin/', admin.site.urls),

    # App-level function-based / class-based view endpoints.
    # IMPORTANT: these are listed BEFORE the router include below so that
    # literal-segment routes (e.g. "destinations/search/") are matched
    # ahead of the router's generic "<prefix>/<pk>/" detail pattern, which
    # would otherwise swallow them (treating "search" as a pk value).
    path('api/v1/accounts/', include('accounts.urls')),
    path('api/v1/destinations/', include('destinations.urls')),
    path('api/v1/itineraries/', include('itineraries.urls')),
    path('api/v1/bookings/', include('bookings.urls')),
    path('api/v1/reviews/', include('reviews.urls')),
    path('api/v1/budgets/', include('budgets.urls')),

    # ViewSet-backed endpoints (router)
    path('api/v1/', include(router.urls)),

    # JWT token refresh (obtain/register live in accounts.urls)
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # API schema & documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
