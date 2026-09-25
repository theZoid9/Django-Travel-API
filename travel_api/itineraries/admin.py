from django.contrib import admin
from .models import Collaboration, DailyPlan, Itinerary


class DailyPlanInline(admin.TabularInline):
    model = DailyPlan
    extra = 0


class CollaborationInline(admin.TabularInline):
    model = Collaboration
    extra = 0


@admin.register(Itinerary)
class ItineraryAdmin(admin.ModelAdmin):
    list_display = ('title', 'destination', 'owner', 'status', 'start_date', 'end_date')
    list_filter = ('status', 'is_public')
    search_fields = ('title', 'destination__name', 'owner__username')
    inlines = [DailyPlanInline, CollaborationInline]


@admin.register(DailyPlan)
class DailyPlanAdmin(admin.ModelAdmin):
    list_display = ('itinerary', 'day_number', 'date', 'title')


@admin.register(Collaboration)
class CollaborationAdmin(admin.ModelAdmin):
    list_display = ('itinerary', 'user', 'role', 'invited_at')
