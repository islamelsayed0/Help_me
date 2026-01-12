from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Includes role and dark mode preference.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
        ('superadmin', 'Superadmin'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        help_text='User role for access control'
    )
    dark_mode_preference = models.BooleanField(
        default=True,
        help_text='User preference for dark mode'
    )
    current_organization = models.ForeignKey(
        'schoolgroups.SchoolGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='active_users',
        help_text='Currently active organization for this user'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']
    
    def __str__(self):
        return self.email or self.username
    
    def is_admin(self):
        """Check if user is admin or superadmin."""
        return self.role in ['admin', 'superadmin']
    
    def is_superadmin(self):
        """Check if user is superadmin."""
        return self.role == 'superadmin'
    
    def has_created_organization(self):
        """Check if user has created an organization."""
        from schoolgroups.models import SchoolGroup
        return SchoolGroup.objects.filter(created_by=self).exists()
    
    def get_created_organization(self):
        """Get the organization this user created, if any."""
        from schoolgroups.models import SchoolGroup
        return SchoolGroup.objects.filter(created_by=self).first()

