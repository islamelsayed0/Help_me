from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin interface for AuditLog model (read-only for superadmins)."""
    list_display = ('id', 'created_at', 'actor', 'action_type', 'resource_type', 'resource_id', 'school_group')
    list_filter = ('action_type', 'resource_type', 'school_group', 'created_at')
    search_fields = ('description', 'actor__email', 'school_group__name', 'resource_type')
    readonly_fields = ('actor', 'school_group', 'action_type', 'resource_type', 'resource_id', 'description', 'metadata', 'created_at')
    
    fieldsets = (
        ('Action', {
            'fields': ('actor', 'action_type', 'description')
        }),
        ('Resource', {
            'fields': ('resource_type', 'resource_id')
        }),
        ('Context', {
            'fields': ('school_group', 'metadata')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable adding audit logs through admin (use utils.log_action instead)."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make audit logs read-only."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow superusers to delete audit logs."""
        return request.user.is_superuser
