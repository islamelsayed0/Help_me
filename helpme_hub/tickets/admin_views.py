"""
Admin-facing ticket views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
import logging

from .models import Ticket
from .forms import UpdateTicketStatusForm, ResolutionNotesForm, AssignTicketForm
from .decorators import admin_ticket_access_required
from accounts.decorators import role_required
from accounts.utils import get_user_school_group
from accounts.models import User

logger = logging.getLogger(__name__)


@login_required
@role_required(['admin', 'superadmin'])
@admin_ticket_access_required
def admin_ticket_board_view(request):
    """Admin Kanban board showing all tickets in their organization."""
    user = request.user
    user_org = get_user_school_group(user)
    
    # Get all tickets from admin's organization
    tickets = Ticket.objects.filter(school_group=user_org)
    
    # Filter by assignee if provided
    assignee_filter = request.GET.get('assignee')
    if assignee_filter == 'me':
        tickets = tickets.filter(assigned_to=user)
    elif assignee_filter == 'unassigned':
        tickets = tickets.filter(assigned_to__isnull=True)
    
    # Organize tickets by status for Kanban columns
    tickets_by_status = {
        'open': tickets.filter(status='open').order_by('-priority', '-created_at'),
        'in_progress': tickets.filter(status='in_progress').order_by('-priority', '-created_at'),
        'resolved': tickets.filter(status='resolved').order_by('-resolved_at'),
        'closed': tickets.filter(status='closed').order_by('-closed_at'),
    }
    
    # Get stats
    stats = {
        'total': tickets.count(),
        'open': tickets.filter(status='open').count(),
        'in_progress': tickets.filter(status='in_progress').count(),
        'resolved': tickets.filter(status='resolved').count(),
        'closed': tickets.filter(status='closed').count(),
        'unassigned': tickets.filter(assigned_to__isnull=True, status__in=['open', 'in_progress']).count(),
    }
    
    # Get admins in organization for assignment dropdown
    org_admins = User.objects.filter(
        role__in=['admin', 'superadmin'],
        memberships__school_group=user_org,
        memberships__status='accepted'
    ).distinct()
    
    context = {
        'tickets_by_status': tickets_by_status,
        'stats': stats,
        'assignee_filter': assignee_filter,
        'org_admins': org_admins,
        'user_org': user_org,
    }
    
    return render(request, 'tickets/admin/board.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@admin_ticket_access_required
def admin_ticket_detail_view(request, ticket_id):
    """Admin view of a specific ticket."""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    user = request.user
    
    # Get linked chat if exists
    try:
        chat = ticket.chat
    except:
        chat = None
    chat_messages = []
    if chat:
        chat_messages = chat.messages.all().order_by('created_at')
    
    # Get admins in organization for assignment
    user_org = get_user_school_group(user)
    org_admins = User.objects.filter(
        role__in=['admin', 'superadmin'],
        memberships__school_group=user_org,
        memberships__status='accepted'
    ).distinct()
    
    # Forms
    status_form = UpdateTicketStatusForm(instance=ticket)
    resolution_form = ResolutionNotesForm()
    assign_form = AssignTicketForm(admins=org_admins, initial={'assigned_to': ticket.assigned_to})
    
    context = {
        'ticket': ticket,
        'chat': chat,
        'chat_messages': chat_messages,
        'status_form': status_form,
        'resolution_form': resolution_form,
        'assign_form': assign_form,
        'org_admins': org_admins,
        'is_assigned': ticket.assigned_to == user,
    }
    
    return render(request, 'tickets/admin/ticket_detail.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@admin_ticket_access_required
@require_http_methods(['POST'])
def assign_ticket_view(request, ticket_id):
    """Admin assigns ticket to themselves or another admin."""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    user = request.user

    if request.POST.get('unassign'):
        ticket.unassign()
        messages.success(request, 'Ticket unassigned.')
        return redirect('tickets:admin_ticket_detail', ticket_id=ticket.id)
    
    user_org = get_user_school_group(user)
    org_admins = User.objects.filter(
        role__in=['admin', 'superadmin'],
        memberships__school_group=user_org,
        memberships__status='accepted'
    ).distinct()
    
    form = AssignTicketForm(request.POST, admins=org_admins)
    if form.is_valid():
        assigned_to = form.cleaned_data.get('assigned_to')
        if assigned_to:
            old_assigned = ticket.assigned_to
            ticket.assign(assigned_to)
            # Log audit action
            from audit.utils import log_ticket_assigned
            log_ticket_assigned(user, ticket, assigned_to)
            
            # Send email notification if assignment changed
            if old_assigned != assigned_to:
                try:
                    from accounts.notifications import send_ticket_assigned_email
                    send_ticket_assigned_email(ticket, assigned_to)
                except Exception as e:
                    logger.error(f'Failed to send ticket assigned email: {str(e)}')
            
            messages.success(request, f'Ticket assigned to {assigned_to.email}.')
        else:
            ticket.unassign()
            messages.success(request, 'Ticket unassigned.')
    else:
        messages.error(request, 'Please correct the errors below.')
    
    return redirect('tickets:admin_ticket_detail', ticket_id=ticket.id)


@login_required
@role_required(['admin', 'superadmin'])
@admin_ticket_access_required
@require_http_methods(['POST'])
def update_ticket_status_view(request, ticket_id):
    """Update ticket status (AJAX endpoint for Kanban board)."""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    user = request.user
    
    new_status = request.POST.get('status')
    new_priority = request.POST.get('priority')
    
    if new_status and new_status in ['open', 'in_progress', 'resolved', 'closed']:
        old_status = ticket.status
        ticket.status = new_status
        if new_status == 'in_progress' and not ticket.assigned_to:
            # Auto-assign if moving to in_progress
            ticket.assigned_to = user
        elif new_status == 'resolved' and not ticket.resolved_at:
            ticket.resolved_at = timezone.now()
        elif new_status == 'closed' and not ticket.closed_at:
            ticket.closed_at = timezone.now()
        
        # Send email notification for status changes
        if old_status != new_status:
            try:
                from accounts.notifications import send_ticket_status_changed_email
                send_ticket_status_changed_email(ticket, user, old_status, new_status)
            except Exception as e:
                logger.error(f'Failed to send ticket status changed email: {str(e)}')
    
    if new_priority and new_priority in ['low', 'medium', 'high', 'urgent']:
        ticket.priority = new_priority
    
    ticket.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'ticket_id': ticket.id,
            'status': ticket.status,
            'priority': ticket.priority,
        })
    
    messages.success(request, 'Ticket status updated.')
    return redirect('tickets:admin_ticket_detail', ticket_id=ticket.id)


@login_required
@role_required(['admin', 'superadmin'])
@admin_ticket_access_required
@require_http_methods(['POST'])
def add_resolution_notes_view(request, ticket_id):
    """Admin adds resolution notes to a ticket."""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    user = request.user
    
    form = ResolutionNotesForm(request.POST)
    if form.is_valid():
        resolution_notes = form.cleaned_data['resolution_notes']
        ticket.resolve(resolution_notes)
        # Log audit action
        from audit.utils import log_ticket_resolved
        log_ticket_resolved(user, ticket)
        messages.success(request, 'Resolution notes added and ticket marked as resolved.')
    else:
        messages.error(request, 'Please correct the errors below.')
    
    return redirect('tickets:admin_ticket_detail', ticket_id=ticket.id)


@login_required
@role_required(['admin', 'superadmin'])
@admin_ticket_access_required
@require_http_methods(['POST'])
def close_ticket_view(request, ticket_id):
    """Admin closes a ticket."""
    ticket = get_object_or_404(Ticket, id=ticket_id)
    user = request.user
    
    resolution_notes = request.POST.get('resolution_notes', '').strip()
    ticket.close(resolution_notes)
    
    # Log audit action
    from audit.utils import log_ticket_closed
    log_ticket_closed(user, ticket)
    
    messages.success(request, 'Ticket closed.')
    return redirect('tickets:admin_ticket_detail', ticket_id=ticket.id)
