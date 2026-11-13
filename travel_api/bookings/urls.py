from django.urls import path
from . import views
app_name = 'bookings'
urlpatterns = [
    path('accommodation-bookings/<int:pk>/', views.AccommodationBookingDetailView.as_view(), name='accommodation_booking_detail'),
    path('activity-bookings/<int:pk>/', views.ActivityBookingDetailView.as_view(), name='activity_booking_detail'),
    path('accommodation-bookings/', views.AccommodationBookingListCreateView.as_view(), name='accommodation_booking_list_create'),
    path('activity-bookings/', views.ActivityBookingListCreateView.as_view(), name='activity_booking_list_create'),
    path('bulk-update/', views.bulk_update_bookings, name='bulk_update_bookings'),
]
