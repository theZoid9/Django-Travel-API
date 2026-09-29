from django.contrib import admin
from .models import Accommodation, Activity, AccommodationBooking, ActivityBooking
admin.site.register(Accommodation)
admin.site.register(Activity)
admin.site.register(AccommodationBooking)
admin.site.register(ActivityBooking)
