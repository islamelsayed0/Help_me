"""
Decorators for ticket views to enforce permissions and organization isolation.
"""
from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Ticket
from accounts.utils import get_user_school_group, has_accepted_membership


def ticket_membership_required(view_func):
    """
    Decorator to ensure user has accepted membership in an organization.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if not has_accepted_membership(request.user):
            messages.info(request, 'You must be a member of an organization to access tickets.')
            return redirect('accounts:pending')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def ticket_owner_required(view_func):
    """
    Decorator to ensure user owns the ticket they're trying to access.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        ticket_id = kwargs.get('ticket_id') or kwargs.get('pk')
        if ticket_id:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            
            # Verify user owns the ticket
            if ticket.user != request.user:
                messages.error(request, 'You do not have permission to access this ticket.')
                return redirect('tickets:ticket_list')
            
            # Verify organization membership
            user_org = get_user_school_group(request.user)
            if not user_org or user_org != ticket.school_group:
                messages.error(request, 'You do not have permission to access this ticket.')
                return redirect('tickets:ticket_list')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_ticket_access_required(view_func):
    """
    Decorator to ensure admin can access tickets from their organization.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if not request.user.is_admin() and not request.user.is_superadmin():
            messages.error(request, 'You must be an admin to access this page.')
            return redirect('accounts:dashboard')
        
        if not has_accepted_membership(request.user):
            messages.info(request, 'You must be a member of an organization to access admin features.')
            return redirect('accounts:pending')
        
        # Verify ticket belongs to admin's organization
        ticket_id = kwargs.get('ticket_id') or kwargs.get('pk')
        if ticket_id:
            ticket = get_object_or_404(Ticket, id=ticket_id)
            user_org = get_user_school_group(request.user)
            
            if not user_org or user_org != ticket.school_group:
                messages.error(request, 'You do not have permission to access this ticket.')
                return redirect('tickets:admin_board')
        
        return view_func(request, *args, **kwargs)
    return wrapper
