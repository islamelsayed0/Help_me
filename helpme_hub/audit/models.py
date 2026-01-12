from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from schoolgroups.models import SchoolGroup
import json

User = get_user_model()


class AuditLog(models.Model):
    """
    Audit log model to track important system actions.
    Records who performed what action on which resource.
    """
    ACTION_TYPE_CHOICES = [
        ('join_request_created', 'Join Request Created'),
        ('join_request_accepted', 'Join Request Accepted'),
        ('join_request_denied', 'Join Request Denied'),
        ('role_changed', 'Role Changed'),
        ('ticket_closed', 'Ticket Closed'),
        ('ticket_assigned', 'Ticket Assigned'),
        ('ticket_resolved', 'Ticket Resolved'),
        ('article_published', 'Article Published'),
        ('article_unpublished', 'Article Unpublished'),
        ('settings_changed', 'Settings Changed'),
    ]
    
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='User who performed the action'
    )
    school_group = models.ForeignKey(
        SchoolGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='Organization context for this action'
    )
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPE_CHOICES,
        help_text='Type of action performed'
    )
    resource_type = models.CharField(
        max_length=100,
        help_text='Type of resource affected (e.g., "JoinRequest", "Ticket", "User")'
    )
    resource_id = models.IntegerField(
        help_text='ID of the affected resource'
    )
    description = models.TextField(
        help_text='Human-readable description of the action'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional context data (JSON object)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['school_group', 'created_at']),
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
    
    def __str__(self):
        actor_name = self.actor.email if self.actor else 'System'
        return f"{actor_name} - {self.get_action_type_display()} - {self.resource_type}#{self.resource_id}"
