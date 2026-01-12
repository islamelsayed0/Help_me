"""
User-facing ticket views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import Ticket
from .forms import EscalateChatForm, CreateTicketForm
from .decorators import ticket_membership_required, ticket_owner_required
from accounts.utils import get_user_school_group, has_accepted_membership
from audit.utils import log_action


@login_required
@ticket_membership_required
@require_http_methods(['GET', 'POST'])
def create_ticket_view(request):
    """Create a new ticket directly."""
    user = request.user
    user_org = get_user_school_group(user)
    
    if request.method == 'POST':
        form = CreateTicketForm(request.POST)
        if form.is_valid():
            ticket = Ticket.objects.create(
                user=user,
                school_group=user_org,
                title=form.cleaned_data['title'],
                description=form.cleaned_data['description'],
                priority=form.cleaned_data['priority'],
                status='open'
            )
            
            # Log ticket creation
            log_action(user, 'ticket_created', 'Ticket', ticket.id, user_org, f'Ticket "{ticket.title}" created by {user.email}')
            
            messages.success(request, f'Ticket #{ticket.id} created successfully!')
            return redirect('tickets:ticket_detail', ticket_id=ticket.id)
    else:
        form = CreateTicketForm()
    
    context = {
        'form': form,
        'user_org': user_org,
    }
    
    return render(request, 'tickets/create_ticket.html', context)


@login_required
@ticket_membership_required
def ticket_list_view(request):
    """List all tickets for the current user."""
    user = request.user
    user_org = get_user_school_group(user)
    
    # Get user's tickets from their current organization
    tickets = Ticket.objects.filter(
        user=user,
        school_group=user_org
    ).order_by('-updated_at', '-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['open', 'in_progress', 'resolved', 'closed']:
        tickets = tickets.filter(status=status_filter)
    
    # Get counts for each status
    status_counts = {
        'all': Ticket.objects.filter(user=user, school_group=user_org).count(),
        'open': Ticket.objects.filter(user=user, school_group=user_org, status='open').count(),
        'in_progress': Ticket.objects.filter(user=user, school_group=user_org, status='in_progress').count(),
        'resolved': Ticket.objects.filter(user=user, school_group=user_org, status='resolved').count(),
        'closed': Ticket.objects.filter(user=user, school_group=user_org, status='closed').count(),
    }
    
    context = {
        'tickets': tickets,
        'status_filter': status_filter,
        'status_counts': status_counts,
        'user_org': user_org,
    }
    
    return render(request, 'tickets/ticket_list.html', context)


@login_required
@ticket_membership_required
@ticket_owner_required
def ticket_detail_view(request, ticket_id):
    """Display ticket details and linked chat transcript."""
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
    
    context = {
        'ticket': ticket,
        'chat': chat,
        'chat_messages': chat_messages,
    }
    
    return render(request, 'tickets/ticket_detail.html', context)
