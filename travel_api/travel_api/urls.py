from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

router = DefaultRouter()

from destinations.views import DestinationViewSet, CategoryViewSet, TagViewSet
router.register(r'destinations', DestinationViewSet, basename='destination')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')

from bookings.views import AccommodationViewSet, ActivityViewSet
router.register(r'accommodations', AccommodationViewSet, basename='accommodation')
router.register(r'activities', ActivityViewSet, basename='activity')

from itineraries.views import ItineraryViewSet, DailyPlanViewSet
router.register(r'itineraries', ItineraryViewSet, basename='itinerary')
router.register(r'daily-plans', DailyPlanViewSet, basename='dailyplan')

from reviews.views import ReviewViewSet, ActivityReviewViewSet
router.register(r'reviews', ReviewViewSet, basename='review')
router.register(r'activity-reviews', ActivityReviewViewSet, basename='activityreview')

from budgets.views import BudgetViewSet, ExpenseViewSet
router.register(r'budgets', BudgetViewSet, basename='budget')
router.register(r'expenses', ExpenseViewSet, basename='expense')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/v1/accounts/', include('accounts.urls')),
    path('api/v1/destinations/', include('destinations.urls')),
    path('api/v1/booking/', include('bookings.urls')),
    path('api/v1/itinerary/', include('itineraries.urls')),
    path('api/v1/reviews-app/', include('reviews.urls')),
    path('api/v1/budgets-app/', include('budgets.urls')),
    path('api/v1/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
