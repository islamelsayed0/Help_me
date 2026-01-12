from django.contrib import admin
from .models import Chat, ChatMessage


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'school_group', 'assigned_to', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'school_group', 'created_at']
    search_fields = ['user__email', 'user__username', 'school_group__name']
    readonly_fields = ['created_at', 'updated_at', 'escalated_at', 'resolved_at']
    raw_id_fields = ['user', 'school_group', 'assigned_to']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'school_group', 'assigned_to', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'escalated_at', 'resolved_at')
        }),
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'chat', 'sender', 'sender_type', 'is_read', 'created_at']
    list_filter = ['sender_type', 'is_read', 'created_at']
    search_fields = ['content', 'chat__user__email', 'sender__email']
    readonly_fields = ['created_at']
    raw_id_fields = ['chat', 'sender']
    
    fieldsets = (
        ('Message', {
            'fields': ('chat', 'sender', 'sender_type', 'content', 'is_read')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
