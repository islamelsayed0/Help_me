from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from schoolgroups.models import SchoolGroup
import json

User = get_user_model()


class Article(models.Model):
    """
    Knowledge base article model.
    Articles can be group-specific or global (school_group=None).
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]
    
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('technical', 'Technical'),
        ('account', 'Account'),
        ('billing', 'Billing'),
        ('other', 'Other'),
    ]
    
    school_group = models.ForeignKey(
        SchoolGroup,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='articles',
        help_text='Organization this article belongs to (null for global articles)'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authored_articles',
        help_text='User who created this article'
    )
    title = models.CharField(
        max_length=255,
        help_text='Article title'
    )
    content = models.TextField(
        help_text='Article content'
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='general',
        help_text='Article category'
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text='Article tags (array of strings)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Article status'
    )
    view_count = models.IntegerField(
        default=0,
        help_text='Number of times article has been viewed'
    )
    helpful_votes = models.IntegerField(
        default=0,
        help_text='Number of helpful votes'
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When article was published'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'school_group']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['school_group', 'status']),
        ]
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
    
    def __str__(self):
        return f"{self.title} ({self.status})"
    
    def publish(self):
        """Publish the article."""
        self.status = 'published'
        if not self.published_at:
            self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at', 'updated_at'])
    
    def unpublish(self):
        """Unpublish the article (set to draft)."""
        self.status = 'draft'
        self.save(update_fields=['status', 'updated_at'])
    
    def increment_view_count(self):
        """Increment the view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def mark_helpful(self):
        """Increment helpful votes."""
        self.helpful_votes += 1
        self.save(update_fields=['helpful_votes'])
    
    def is_published(self):
        """Check if article is published."""
        return self.status == 'published'
    
    def is_global(self):
        """Check if article is global (not group-specific)."""
        return self.school_group is None
    
    def get_excerpt(self, length=200):
        """Get excerpt of content."""
        if len(self.content) <= length:
            return self.content
        return self.content[:length] + '...'
