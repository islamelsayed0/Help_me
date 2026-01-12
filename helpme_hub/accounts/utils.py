"""
Utility functions for membership and organization management.
"""
from schoolgroups.models import SchoolGroupMembership, SchoolGroup


def get_user_school_group(user):
    """
    Get user's current organization.
    Uses current_organization if set, otherwise returns first accepted membership.
    """
    if not user or not user.is_authenticated:
        return None
    
    # Use current_organization if set and user is a member
    if user.current_organization:
        membership = SchoolGroupMembership.objects.filter(
            user=user,
            school_group=user.current_organization,
            status='accepted'
        ).first()
        if membership:
            return user.current_organization
    
    # Fallback to first accepted membership
    membership = SchoolGroupMembership.objects.filter(
        user=user,
        status='accepted'
    ).select_related('school_group').first()
    
    if membership:
        # Update current_organization if not set
        if not user.current_organization:
            user.current_organization = membership.school_group
            user.save(update_fields=['current_organization'])
        return membership.school_group
    
    return None


def has_accepted_membership(user):
    """
    Check if user has an accepted membership in any organization.
    """
    if not user or not user.is_authenticated:
        return False
    
    return SchoolGroupMembership.objects.filter(
        user=user,
        status='accepted'
    ).exists()


def get_user_organizations(user):
    """
    Get all organizations user is a member of (accepted status).
    Returns queryset of SchoolGroup objects.
    """
    if not user or not user.is_authenticated:
        return SchoolGroup.objects.none()
    
    return SchoolGroup.objects.filter(
        memberships__user=user,
        memberships__status='accepted'
    ).distinct().order_by('name')


def get_user_memberships(user):
    """
    Get all memberships for a user.
    Returns queryset of SchoolGroupMembership objects.
    """
    if not user or not user.is_authenticated:
        return SchoolGroupMembership.objects.none()
    
    return SchoolGroupMembership.objects.filter(
        user=user
    ).select_related('school_group').order_by('-created_at')


def get_user_pending_join_request(user, school_group=None):
    """
    Get user's pending join request for an organization.
    If school_group is None, returns first pending request.
    """
    if not user or not user.is_authenticated:
        return None
    
    from schoolgroups.models import JoinRequest
    
    queryset = JoinRequest.objects.filter(
        user=user,
        status='pending'
    )
    
    if school_group:
        queryset = queryset.filter(school_group=school_group)
    
    return queryset.first()

