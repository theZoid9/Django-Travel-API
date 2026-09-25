from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'rating', 'target_name', 'created_at')
    list_filter = ('rating',)
    search_fields = ('title', 'content', 'user__username')
