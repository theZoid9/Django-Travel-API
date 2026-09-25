"""bookings/urls.py"""
from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('bulk-update/', views.bulk_update_bookings, name='bulk-update'),
    # Namespaced under "manage/" so this CBV doesn't shadow the ModelViewSet's
    # own "<pk>/" retrieve/update/destroy route registered via the router.
    path('manage/<int:pk>/', views.BookingDetailView.as_view(), name='booking-detail'),
]
