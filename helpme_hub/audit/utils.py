"""
Utility functions for audit logging.
"""
from django.contrib.auth import get_user_model
from .models import AuditLog
from schoolgroups.models import SchoolGroup

User = get_user_model()


def log_action(actor, action_type, resource_type, resource_id, school_group=None, description=None, metadata=None):
    """
    Create an audit log entry.
    
    Args:
        actor: User who performed the action (User instance or None)
        action_type: Type of action (string from ACTION_TYPE_CHOICES)
        resource_type: Type of resource affected (string, e.g., 'JoinRequest', 'Ticket')
        resource_id: ID of the affected resource (integer)
        school_group: SchoolGroup instance (optional)
        description: Human-readable description (optional, will be auto-generated if not provided)
        metadata: Additional context data (dict, optional)
    
    Returns:
        AuditLog instance
    """
    # Auto-generate description if not provided
    if not description:
        action_display = dict(AuditLog.ACTION_TYPE_CHOICES).get(action_type, action_type)
        resource_name = resource_type.replace('_', ' ').title()
        if actor:
            description = f"{actor.email} {action_display.lower()} {resource_name} #{resource_id}"
        else:
            description = f"System {action_display.lower()} {resource_name} #{resource_id}"
    
    audit_log = AuditLog.objects.create(
        actor=actor,
        school_group=school_group,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        description=description,
        metadata=metadata or {}
    )
    
    return audit_log


def log_join_request_created(actor, join_request):
    """Log join request creation."""
    return log_action(
        actor=actor,
        action_type='join_request_created',
        resource_type='JoinRequest',
        resource_id=join_request.id,
        school_group=join_request.school_group,
        description=f"{actor.email} requested to join {join_request.school_group.name}",
        metadata={
            'user_email': actor.email,
            'school_group_name': join_request.school_group.name,
            'school_group_id': join_request.school_group.id,
        }
    )


def log_join_request_accepted(actor, join_request):
    """Log join request acceptance."""
    return log_action(
        actor=actor,
        action_type='join_request_accepted',
        resource_type='JoinRequest',
        resource_id=join_request.id,
        school_group=join_request.school_group,
        description=f"{actor.email} accepted join request from {join_request.user.email} to {join_request.school_group.name}",
        metadata={
            'reviewer_email': actor.email,
            'user_email': join_request.user.email,
            'school_group_name': join_request.school_group.name,
            'school_group_id': join_request.school_group.id,
        }
    )


def log_join_request_denied(actor, join_request):
    """Log join request denial."""
    return log_action(
        actor=actor,
        action_type='join_request_denied',
        resource_type='JoinRequest',
        resource_id=join_request.id,
        school_group=join_request.school_group,
        description=f"{actor.email} denied join request from {join_request.user.email} to {join_request.school_group.name}",
        metadata={
            'reviewer_email': actor.email,
            'user_email': join_request.user.email,
            'school_group_name': join_request.school_group.name,
            'school_group_id': join_request.school_group.id,
            'notes': join_request.notes,
        }
    )


def log_role_changed(actor, user, old_role, new_role, school_group=None):
    """Log role change."""
    return log_action(
        actor=actor,
        action_type='role_changed',
        resource_type='User',
        resource_id=user.id,
        school_group=school_group,
        description=f"{actor.email} changed {user.email}'s role from {old_role} to {new_role}",
        metadata={
            'reviewer_email': actor.email,
            'user_email': user.email,
            'old_role': old_role,
            'new_role': new_role,
        }
    )


def log_ticket_closed(actor, ticket):
    """Log ticket closure."""
    return log_action(
        actor=actor,
        action_type='ticket_closed',
        resource_type='Ticket',
        resource_id=ticket.id,
        school_group=ticket.school_group,
        description=f"{actor.email} closed ticket #{ticket.id}: {ticket.title}",
        metadata={
            'user_email': actor.email,
            'ticket_title': ticket.title,
            'ticket_status': ticket.status,
            'school_group_name': ticket.school_group.name,
            'school_group_id': ticket.school_group.id,
        }
    )


def log_ticket_assigned(actor, ticket, assigned_to):
    """Log ticket assignment."""
    return log_action(
        actor=actor,
        action_type='ticket_assigned',
        resource_type='Ticket',
        resource_id=ticket.id,
        school_group=ticket.school_group,
        description=f"{actor.email} assigned ticket #{ticket.id} to {assigned_to.email}",
        metadata={
            'assigner_email': actor.email,
            'assigned_to_email': assigned_to.email,
            'ticket_title': ticket.title,
            'school_group_name': ticket.school_group.name,
            'school_group_id': ticket.school_group.id,
        }
    )


def log_ticket_resolved(actor, ticket):
    """Log ticket resolution."""
    return log_action(
        actor=actor,
        action_type='ticket_resolved',
        resource_type='Ticket',
        resource_id=ticket.id,
        school_group=ticket.school_group,
        description=f"{actor.email} resolved ticket #{ticket.id}: {ticket.title}",
        metadata={
            'user_email': actor.email,
            'ticket_title': ticket.title,
            'school_group_name': ticket.school_group.name,
            'school_group_id': ticket.school_group.id,
        }
    )


def log_article_published(actor, article):
    """Log article publication."""
    return log_action(
        actor=actor,
        action_type='article_published',
        resource_type='Article',
        resource_id=article.id,
        school_group=article.school_group,
        description=f"{actor.email} published article: {article.title}",
        metadata={
            'author_email': actor.email,
            'article_title': article.title,
            'article_category': article.category,
            'school_group_name': article.school_group.name if article.school_group else None,
            'school_group_id': article.school_group.id if article.school_group else None,
        }
    )


def log_article_unpublished(actor, article):
    """Log article unpublishing."""
    return log_action(
        actor=actor,
        action_type='article_unpublished',
        resource_type='Article',
        resource_id=article.id,
        school_group=article.school_group,
        description=f"{actor.email} unpublished article: {article.title}",
        metadata={
            'author_email': actor.email,
            'article_title': article.title,
            'article_category': article.category,
            'school_group_name': article.school_group.name if article.school_group else None,
            'school_group_id': article.school_group.id if article.school_group else None,
        }
    )


def log_settings_changed(actor, setting_name, old_value, new_value, school_group=None):
    """Log settings change."""
    return log_action(
        actor=actor,
        action_type='settings_changed',
        resource_type='Settings',
        resource_id=0,  # Settings don't have an ID
        school_group=school_group,
        description=f"{actor.email} changed setting {setting_name}",
        metadata={
            'user_email': actor.email,
            'setting_name': setting_name,
            'old_value': str(old_value),
            'new_value': str(new_value),
        }
    )
