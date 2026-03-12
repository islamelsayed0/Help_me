from django.contrib import admin
from .models import Ticket, TicketComment


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'school_group', 'assigned_to', 'status', 'priority', 'source', 'created_at', 'updated_at']
    list_filter = ['status', 'priority', 'source', 'school_group', 'created_at']
    search_fields = ['title', 'description', 'user__email', 'user__username', 'school_group__name']
    readonly_fields = ['created_at', 'updated_at', 'resolved_at', 'closed_at']
    raw_id_fields = ['user', 'school_group', 'assigned_to', 'chat']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'user', 'school_group', 'chat', 'source')
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


@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'ticket', 'author', 'is_internal', 'created_at']
    list_filter = ['is_internal', 'created_at']
    search_fields = ['body', 'author__email', 'ticket__title']
    readonly_fields = ['created_at']
    raw_id_fields = ['ticket', 'author']
