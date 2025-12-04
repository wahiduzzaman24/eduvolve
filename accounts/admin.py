from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Badge, UserBadge

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'role', 'total_points', 'current_streak', 'date_joined']
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'bio', 'profile_picture', 'phone', 'date_of_birth')
        }),
        ('Gamification', {
            'fields': ('total_points', 'current_streak', 'longest_streak', 'last_activity_date')
        }),
    )


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'points_required', 'color', 'created_at']
    search_fields = ['name', 'description']


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'earned_at']
    list_filter = ['badge', 'earned_at']
    search_fields = ['user__username', 'badge__name']