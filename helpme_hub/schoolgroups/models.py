from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import IntegrityError
import random
import string
from datetime import timedelta

User = get_user_model()

# Plan choices for subscription
PLAN_CHOICES = [
    ('free', 'Free'),
    ('pro', 'Pro'),
    ('enterprise', 'Enterprise'),
]

# AI plan choices
AI_PLAN_CHOICES = [
    ('limited', 'Limited'),
    ('unlimited', 'Unlimited'),
]


class SchoolGroup(models.Model):
    """
    Organization model with subscription management.
    Represents an organization that users can join or create.
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text='Name of the organization'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of the organization'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether the organization is active'
    )
    
    # Subscription fields
    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default='free',
        help_text='Subscription plan for this organization'
    )
    admin_limit = models.IntegerField(
        default=1,
        help_text='Maximum number of admins allowed (1 for Free, 10 for Pro, custom for Enterprise)'
    )
    ai_enabled = models.BooleanField(
        default=False,
        help_text='Whether AI Add-On is enabled'
    )
    ai_plan = models.CharField(
        max_length=20,
        choices=AI_PLAN_CHOICES,
        default='limited',
        help_text='AI assistance level: limited or unlimited'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_organizations',
        help_text='User who created this organization'
    )
    
    # Access code fields
    access_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text='Randomly generated access code for joining this organization'
    )
    access_code_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the access code was generated'
    )
    access_code_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the access code expires (default: 30 days from generation)'
    )
    
    class Meta:
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_admin_count(self):
        """Get current number of admins in this organization."""
        return self.memberships.filter(
            user__role__in=['admin', 'superadmin'],
            status='accepted'
        ).count()
    
    def get_members(self):
        """Get all accepted members of this school group."""
        return User.objects.filter(
            memberships__school_group=self,
            memberships__status='accepted'
        ).distinct()
    
    def has_member(self, user):
        """Check if user is an accepted member of this school group."""
        return self.memberships.filter(
            user=user,
            status='accepted'
        ).exists()
    
    def can_join(self, user):
        """Check if user can join this organization."""
        # Check if user already has a membership (any status)
        if self.memberships.filter(user=user).exists():
            return False
        # Check if organization is active
        return self.is_active
    
    def get_creator(self):
        """Get the user who created this organization."""
        if self.created_by:
            return self.created_by
        # Fallback: find first admin membership (for backward compatibility)
        first_admin = self.memberships.filter(
            user__role__in=['admin', 'superadmin'],
            status='accepted'
        ).order_by('joined_at', 'created_at').first()
        return first_admin.user if first_admin else None
    
    def can_add_admin(self):
        """Check if organization can add more admins."""
        return self.get_admin_count() < self.admin_limit
    
    def get_ai_status(self):
        """Get AI status display text."""
        if self.ai_enabled and self.ai_plan == 'unlimited':
            return 'Unlimited AI'
        return 'Limited AI'
    
    def get_plan_price(self):
        """Get display price for current plan."""
        if self.plan == 'free':
            return '$0'
        elif self.plan == 'pro':
            return '$59/month'
        elif self.plan == 'enterprise':
            return 'Custom pricing'
        return 'N/A'
    
    def generate_access_code(self):
        """
        Generate a random 12+ character alphanumeric access code.
        Format: uppercase alphanumeric, 12 characters minimum.
        Returns the generated code.
        """
        # Generate 12-character code using uppercase letters and digits
        code_length = 12
        characters = string.ascii_uppercase + string.digits
        # Exclude confusing characters: 0, O, I, 1
        characters = characters.replace('0', '').replace('O', '').replace('I', '').replace('1', '')
        
        max_attempts = 100
        for _ in range(max_attempts):
            code = ''.join(random.choice(characters) for _ in range(code_length))
            # Check if code already exists
            if not SchoolGroup.objects.filter(access_code=code).exclude(pk=self.pk).exists():
                self.access_code = code
                self.access_code_generated_at = timezone.now()
                # Set expiry to 30 days from generation
                self.access_code_expires_at = self.access_code_generated_at + timedelta(days=30)
                self.save(update_fields=['access_code', 'access_code_generated_at', 'access_code_expires_at'])
                return code
        
        # Fallback: if all attempts failed (very unlikely), raise error
        raise ValueError('Unable to generate unique access code after multiple attempts.')
    
    def is_access_code_valid(self):
        """
        Check if the access code exists and hasn't expired.
        Returns True if code is valid, False otherwise.
        """
        if not self.access_code:
            return False
        
        if not self.access_code_expires_at:
            return True  # No expiry set, consider valid
        
        return timezone.now() <= self.access_code_expires_at
    
    def regenerate_access_code(self):
        """
        Regenerate the access code for this organization.
        Invalidates the old code and generates a new one.
        Returns the new code.
        """
        return self.generate_access_code()
    
    @staticmethod
    def format_access_code(code):
        """
        Format an access code with dashes for display.
        Takes a code string (with or without dashes) and returns formatted code: XXXX-XXXX-XXXX
        """
        if not code:
            return ''
        # Remove any existing dashes and spaces
        normalized = code.replace('-', '').replace(' ', '').upper()
        # Format as XXXX-XXXX-XXXX
        if len(normalized) >= 12:
            return f"{normalized[0:4]}-{normalized[4:8]}-{normalized[8:12]}"
        return normalized  # Return as-is if not 12 characters
    
    @staticmethod
    def normalize_access_code(code):
        """
        Normalize an access code for database lookup.
        Removes dashes, spaces, and converts to uppercase.
        """
        if not code:
            return ''
        return code.replace('-', '').replace(' ', '').upper()
    
    def get_formatted_access_code(self):
        """
        Get the formatted access code for this organization.
        Returns the code with dashes for display.
        """
        if not self.access_code:
            return ''
        return self.format_access_code(self.access_code)
    
    # Stripe fields
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True, help_text='Stripe customer ID')
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True, help_text='Stripe subscription ID')
    subscription_status = models.CharField(max_length=50, blank=True, null=True, help_text='Current subscription status from Stripe')
    subscription_current_period_end = models.DateTimeField(null=True, blank=True, help_text='When the current subscription period ends')


class SchoolGroupMembership(models.Model):
    """
    Links users to organizations with status tracking.
    Represents a user's membership in an organization.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('denied', 'Denied'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memberships',
        help_text='User who is a member'
    )
    school_group = models.ForeignKey(
        SchoolGroup,
        on_delete=models.CASCADE,
        related_name='memberships',
        help_text='School group the user belongs to'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Membership status'
    )
    joined_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the user was accepted into the group'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Organization Membership'
        verbose_name_plural = 'Organization Memberships'
        unique_together = [['user', 'school_group']]
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['school_group', 'status']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.email} - {self.school_group.name} ({self.status})'
    
    def accept(self, reviewed_by=None):
        """Accept the membership request."""
        self.status = 'accepted'
        self.joined_at = timezone.now()
        self.save()
        return self
    
    def deny(self):
        """Deny the membership request."""
        self.status = 'denied'
        self.save()
        return self
    
    def is_accepted(self):
        """Check if membership is accepted."""
        return self.status == 'accepted'


class JoinRequest(models.Model):
    """
    Tracks join requests separately from memberships.
    Represents a user's request to join an organization.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('denied', 'Denied'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='join_requests',
        help_text='User requesting to join'
    )
    school_group = models.ForeignKey(
        SchoolGroup,
        on_delete=models.CASCADE,
        related_name='join_requests',
        help_text='School group being requested'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Request status'
    )
    requested_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the request was made'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the request was reviewed'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_join_requests',
        help_text='Admin who reviewed the request'
    )
    notes = models.TextField(
        blank=True,
        help_text='Admin notes about the request'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Join Request'
        verbose_name_plural = 'Join Requests'
        indexes = [
            models.Index(fields=['school_group', 'status']),
            models.Index(fields=['user', 'status']),
        ]
        ordering = ['-requested_at']
    
    def __str__(self):
        return f'{self.user.email} -> {self.school_group.name} ({self.status})'
    
    def accept(self, reviewed_by=None):
        """Accept the join request."""
        self.status = 'accepted'
        self.reviewed_at = timezone.now()
        if reviewed_by:
            self.reviewed_by = reviewed_by
        self.save()
        
        # Update or create membership
        try:
            membership, created = SchoolGroupMembership.objects.get_or_create(
                user=self.user,
                school_group=self.school_group,
                defaults={'status': 'accepted', 'joined_at': timezone.now()}
            )
            if not created:
                membership.accept()
        except IntegrityError:
            # Race condition: membership was created by another process between check and create
            # Get the existing membership and update it
            membership = SchoolGroupMembership.objects.get(
                user=self.user,
                school_group=self.school_group
            )
            membership.accept()
        
        return self
    
    def deny(self, reviewed_by=None, notes=''):
        """Deny the join request."""
        self.status = 'denied'
        self.reviewed_at = timezone.now()
        if reviewed_by:
            self.reviewed_by = reviewed_by
        if notes:
            self.notes = notes
        self.save()
        
        # Update membership status if exists
        try:
            membership = SchoolGroupMembership.objects.get(
                user=self.user,
                school_group=self.school_group
            )
            membership.deny()
        except SchoolGroupMembership.DoesNotExist:
            # Create denied membership record
            SchoolGroupMembership.objects.create(
                user=self.user,
                school_group=self.school_group,
                status='denied'
            )
        
        return self


class StripeWebhookEvent(models.Model):
    """Processed Stripe webhook events for idempotency (at-most-once handling)."""

    stripe_event_id = models.CharField(max_length=255, unique=True, db_index=True)
    event_type = models.CharField(max_length=255, blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Stripe webhook event'
        verbose_name_plural = 'Stripe webhook events'
        ordering = ['-created_at']

    def __str__(self):
        return self.stripe_event_id
