"""
Template tags for schoolgroups app.
"""
from django import template
from schoolgroups.models import JoinRequest
from accounts.utils import get_user_school_group

register = template.Library()


@register.simple_tag
def get_pending_join_requests_count(user):
    """
    Get the count of pending join requests for the user's school group.
    For admins, returns count for their school group.
    For superadmins, returns count for all school groups.
    """
    if not user or not user.is_authenticated:
        return 0
    
    if user.is_superadmin():
        # Superadmins see all pending requests
        return JoinRequest.objects.filter(status='pending').count()
    elif user.is_admin():
        # Regular admins see requests for their school group
        school_group = get_user_school_group(user)
        if school_group:
            return JoinRequest.objects.filter(
                school_group=school_group,
                status='pending'
            ).count()
    
    return 0


