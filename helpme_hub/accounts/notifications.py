"""
Email notification utilities for key system events.
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_welcome_email(user):
    """
    Send welcome email to newly registered user.
    
    Args:
        user: User instance
    """
    try:
        subject = 'Welcome to HelpMe Hub!'
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        site_url = f"https://{site.domain}" if not site.domain.startswith('http') else site.domain
        
        html_message = render_to_string('accounts/emails/welcome.html', {
            'user': user,
            'site_name': 'HelpMe Hub',
            'site_url': site_url,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Welcome email sent to {user.email}')
    except Exception as e:
        logger.error(f'Error sending welcome email to {user.email}: {str(e)}')


def send_join_request_approved_email(user, school_group):
    """
    Send email notification when join request is approved.
    
    Args:
        user: User instance
        school_group: SchoolGroup instance
    """
    try:
        subject = f'Your request to join {school_group.name} has been approved'
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        site_url = f"https://{site.domain}" if not site.domain.startswith('http') else site.domain
        
        html_message = render_to_string('accounts/emails/join_request_approved.html', {
            'user': user,
            'school_group': school_group,
            'site_name': 'HelpMe Hub',
            'site_url': site_url,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Join request approved email sent to {user.email}')
    except Exception as e:
        logger.error(f'Error sending join request approved email to {user.email}: {str(e)}')


def send_join_request_denied_email(user, school_group, notes=''):
    """
    Send email notification when join request is denied.
    
    Args:
        user: User instance
        school_group: SchoolGroup instance
        notes: Optional notes from reviewer
    """
    try:
        subject = f'Your request to join {school_group.name}'
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        site_url = f"https://{site.domain}" if not site.domain.startswith('http') else site.domain
        
        html_message = render_to_string('accounts/emails/join_request_denied.html', {
            'user': user,
            'school_group': school_group,
            'notes': notes,
            'site_name': 'HelpMe Hub',
            'site_url': site_url,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Join request denied email sent to {user.email}')
    except Exception as e:
        logger.error(f'Error sending join request denied email to {user.email}: {str(e)}')


def send_ticket_assigned_email(ticket, assigned_to):
    """
    Send email notification when ticket is assigned.
    
    Args:
        ticket: Ticket instance
        assigned_to: User instance (who was assigned)
    """
    try:
        subject = f'New ticket assigned: {ticket.title}'
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        site_url = f"https://{site.domain}" if not site.domain.startswith('http') else site.domain
        
        html_message = render_to_string('tickets/emails/ticket_assigned.html', {
            'ticket': ticket,
            'assigned_to': assigned_to,
            'site_name': 'HelpMe Hub',
            'site_url': site_url,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[assigned_to.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Ticket assigned email sent to {assigned_to.email}')
    except Exception as e:
        logger.error(f'Error sending ticket assigned email to {assigned_to.email}: {str(e)}')


def send_ticket_status_changed_email(ticket, user, old_status, new_status):
    """
    Send email notification when ticket status changes.
    
    Args:
        ticket: Ticket instance
        user: User instance (who made the change)
        old_status: Previous status
        new_status: New status
    """
    try:
        # Only send to ticket creator if status is resolved or closed
        if new_status in ['resolved', 'closed']:
            subject = f'Ticket #{ticket.id} has been {new_status}'
            from django.contrib.sites.models import Site
            site = Site.objects.get_current()
            site_url = f"https://{site.domain}" if not site.domain.startswith('http') else site.domain
            
            html_message = render_to_string('tickets/emails/ticket_status_changed.html', {
                'ticket': ticket,
                'user': user,
                'old_status': old_status,
                'new_status': new_status,
                'site_name': 'HelpMe Hub',
                'site_url': site_url,
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[ticket.created_by.email],
                html_message=html_message,
                fail_silently=False,
            )
            logger.info(f'Ticket status changed email sent to {ticket.created_by.email}')
    except Exception as e:
        logger.error(f'Error sending ticket status changed email: {str(e)}')


def send_chat_escalated_email(chat, ticket):
    """
    Send email notification when chat is escalated to ticket.
    
    Args:
        chat: Chat instance
        ticket: Ticket instance (created from escalation)
    """
    try:
        subject = f'Your chat has been escalated to ticket #{ticket.id}'
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        site_url = f"https://{site.domain}" if not site.domain.startswith('http') else site.domain
        
        html_message = render_to_string('chats/emails/chat_escalated.html', {
            'chat': chat,
            'ticket': ticket,
            'site_name': 'HelpMe Hub',
            'site_url': site_url,
        })
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[chat.created_by.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Chat escalated email sent to {chat.created_by.email}')
    except Exception as e:
        logger.error(f'Error sending chat escalated email: {str(e)}')
