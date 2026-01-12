from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from schoolgroups.models import SchoolGroup

User = get_user_model()


class Ticket(models.Model):
    """
    Ticket model for escalated support requests.
    Created when a chat is escalated or can be created directly.
    """
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    chat = models.OneToOneField(
        'chats.Chat',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ticket',
        help_text='Chat this ticket was escalated from (if any)'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tickets',
        help_text='User who created the ticket'
    )
    school_group = models.ForeignKey(
        SchoolGroup,
        on_delete=models.CASCADE,
        related_name='tickets',
        help_text='Organization this ticket belongs to'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        help_text='Admin assigned to this ticket'
    )
    title = models.CharField(
        max_length=255,
        help_text='Ticket title'
    )
    description = models.TextField(
        help_text='Ticket description'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        help_text='Current status of the ticket'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text='Priority level of the ticket'
    )
    resolution_notes = models.TextField(
        blank=True,
        null=True,
        help_text='Resolution notes added when ticket is resolved'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When ticket was marked as resolved'
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When ticket was closed'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['school_group', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['status', 'priority']),
        ]
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
    
    def __str__(self):
        return f"Ticket #{self.id} - {self.title} ({self.status})"
    
    def can_assign(self):
        """Check if ticket can be assigned."""
        return self.status in ['open', 'in_progress']
    
    def can_resolve(self):
        """Check if ticket can be marked as resolved."""
        return self.status in ['open', 'in_progress']
    
    def can_close(self):
        """Check if ticket can be closed."""
        return self.status in ['resolved', 'open', 'in_progress']
    
    def assign(self, admin_user):
        """Assign ticket to an admin."""
        if self.can_assign():
            self.assigned_to = admin_user
            if self.status == 'open':
                self.status = 'in_progress'
            self.save(update_fields=['assigned_to', 'status', 'updated_at'])
    
    def unassign(self):
        """Unassign ticket from admin."""
        self.assigned_to = None
        if self.status == 'in_progress':
            self.status = 'open'
        self.save(update_fields=['assigned_to', 'status', 'updated_at'])
    
    def resolve(self, resolution_notes=''):
        """Mark ticket as resolved."""
        if self.can_resolve():
            self.status = 'resolved'
            self.resolved_at = timezone.now()
            if resolution_notes:
                self.resolution_notes = resolution_notes
            self.save(update_fields=['status', 'resolved_at', 'resolution_notes', 'updated_at'])
    
    def close(self, resolution_notes=''):
        """Close the ticket."""
        if self.can_close():
            self.status = 'closed'
            self.closed_at = timezone.now()
            if resolution_notes and not self.resolution_notes:
                self.resolution_notes = resolution_notes
            self.save(update_fields=['status', 'closed_at', 'resolution_notes', 'updated_at'])
