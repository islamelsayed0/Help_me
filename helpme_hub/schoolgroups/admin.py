from django.contrib import admin
from .models import SchoolGroup, SchoolGroupMembership, JoinRequest


@admin.register(SchoolGroup)
class SchoolGroupAdmin(admin.ModelAdmin):
    """Admin interface for SchoolGroup model."""
    list_display = ('name', 'plan', 'admin_limit', 'ai_enabled', 'ai_plan', 'is_active', 'created_at')
    list_filter = ('plan', 'ai_enabled', 'ai_plan', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Subscription', {
            'fields': ('plan', 'admin_limit', 'ai_enabled', 'ai_plan')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(SchoolGroupMembership)
class SchoolGroupMembershipAdmin(admin.ModelAdmin):
    """Admin interface for SchoolGroupMembership model."""
    list_display = ('user', 'school_group', 'status', 'joined_at', 'created_at')
    list_filter = ('status', 'school_group', 'created_at')
    search_fields = ('user__email', 'user__username', 'school_group__name')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('user', 'school_group')


@admin.register(JoinRequest)
class JoinRequestAdmin(admin.ModelAdmin):
    """Admin interface for JoinRequest model."""
    list_display = ('user', 'school_group', 'status', 'requested_at', 'reviewed_at', 'reviewed_by')
    list_filter = ('status', 'school_group', 'requested_at', 'reviewed_at')
    search_fields = ('user__email', 'user__username', 'school_group__name', 'notes')
    readonly_fields = ('requested_at', 'created_at', 'updated_at')
    autocomplete_fields = ('user', 'school_group', 'reviewed_by')
