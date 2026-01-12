from django.contrib import admin
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'school_group', 'assigned_to', 'status', 'priority', 'created_at', 'updated_at']
    list_filter = ['status', 'priority', 'school_group', 'created_at']
    search_fields = ['title', 'description', 'user__email', 'user__username', 'school_group__name']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at', 'closed_at']
    raw_id_fields = ['user', 'school_group', 'assigned_to', 'chat']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'user', 'school_group', 'chat')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'status', 'priority')
        }),
        ('Resolution', {
            'fields': ('resolution_notes', 'resolved_at', 'closed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
