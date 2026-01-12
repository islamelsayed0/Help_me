from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from schoolgroups.models import SchoolGroup

User = get_user_model()


class Chat(models.Model):
    """
    Chat model representing a support conversation.
    Users create chats, admins can assign themselves, and AI can respond.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('escalated', 'Escalated'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chats',
        help_text='User who created the chat'
    )
    school_group = models.ForeignKey(
        SchoolGroup,
        on_delete=models.CASCADE,
        related_name='chats',
        help_text='Organization this chat belongs to'
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_chats',
        help_text='Admin assigned to this chat'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text='Current status of the chat'
    )
    escalated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When chat was escalated to ticket'
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When chat was marked as resolved'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['school_group', 'status']),
            models.Index(fields=['assigned_to', 'status']),
        ]
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'
    
    def __str__(self):
        return f"Chat #{self.id} - {self.user.email} ({self.status})"
    
    def can_escalate(self):
        """Check if chat can be escalated to ticket."""
        return self.status == 'active'
    
    def can_resolve(self):
        """Check if chat can be marked as resolved."""
        return self.status == 'active'
    
    def get_unread_count(self, user):
        """Get count of unread messages for a specific user."""
        if user == self.user:
            # For users, count unread admin and AI messages
            return self.messages.filter(
                sender_type__in=['admin', 'ai'],
                is_read=False
            ).count()
        else:
            # For admins, count unread user messages
            return self.messages.filter(
                sender_type='user',
                is_read=False
            ).count()
    
    def mark_all_read(self, user):
        """Mark all messages as read for a specific user."""
        if user == self.user:
            # Mark admin and AI messages as read
            self.messages.filter(
                sender_type__in=['admin', 'ai'],
                is_read=False
            ).update(is_read=True)
        else:
            # Mark user messages as read
            self.messages.filter(
                sender_type='user',
                is_read=False
            ).update(is_read=True)
    
    def get_last_message(self):
        """Get the last message in this chat."""
        return self.messages.order_by('-created_at').first()
    
    def escalate(self):
        """Mark chat as escalated (ticket creation handled in views)."""
        if self.can_escalate():
            self.status = 'escalated'
            self.escalated_at = timezone.now()
            self.save(update_fields=['status', 'escalated_at', 'updated_at'])
    
    def resolve(self):
        """Mark chat as resolved."""
        if self.can_resolve():
            self.status = 'resolved'
            self.resolved_at = timezone.now()
            self.save(update_fields=['status', 'resolved_at', 'updated_at'])
    
    def close(self):
        """Close the chat."""
        self.status = 'closed'
        self.save(update_fields=['status', 'updated_at'])


class ChatMessage(models.Model):
    """
    Individual message within a chat.
    Can be from user, admin, or AI.
    """
    SENDER_TYPE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
        ('ai', 'AI'),
    ]
    
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text='Chat this message belongs to'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        null=True,
        blank=True,
        help_text='User who sent the message (null for AI messages)'
    )
    sender_type = models.CharField(
        max_length=10,
        choices=SENDER_TYPE_CHOICES,
        help_text='Type of sender (user, admin, or AI)'
    )
    content = models.TextField(
        help_text='Message content'
    )
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the message has been read'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['chat', 'created_at']),
            models.Index(fields=['chat', 'is_read']),
        ]
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
    
    def __str__(self):
        sender_name = self.sender.email if self.sender else 'AI'
        return f"Message from {sender_name} in Chat #{self.chat.id}"
    
    def mark_as_read(self):
        """Mark this message as read."""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
