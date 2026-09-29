from django.contrib import admin
from .models import Itinerary, TripCollaborator, DailyPlan, DayActivity, ActivityLog
admin.site.register(Itinerary)
admin.site.register(DailyPlan)
admin.site.register(DayActivity)
admin.site.register(ActivityLog)
