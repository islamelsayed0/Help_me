"""
Admin-facing chat views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q, Count, Max
from django.utils import timezone

from .models import Chat, ChatMessage
from .forms import ChatMessageForm
from .decorators import admin_chat_access_required
from accounts.decorators import role_required
from accounts.utils import get_user_school_group


@login_required
@role_required(['admin', 'superadmin'])
@admin_chat_access_required
def admin_chat_inbox_view(request):
    """Admin inbox showing all chats in their organization."""
    user = request.user
    user_org = get_user_school_group(user)
    
    # Get all chats from admin's organization
    chats = Chat.objects.filter(
        school_group=user_org
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count('messages', filter=Q(
            messages__sender_type='user',
            messages__is_read=False
        ))
    ).order_by('-updated_at', '-created_at')
    
    # Filters
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['active', 'escalated', 'resolved', 'closed']:
        chats = chats.filter(status=status_filter)
    
    assigned_filter = request.GET.get('assigned')
    if assigned_filter == 'me':
        chats = chats.filter(assigned_to=user)
    elif assigned_filter == 'unassigned':
        chats = chats.filter(assigned_to__isnull=True)
    
    unread_only = request.GET.get('unread') == 'true'
    if unread_only:
        chats = chats.filter(unread_count__gt=0)
    
    # Stats
    total_chats = Chat.objects.filter(school_group=user_org).count()
    unassigned_count = Chat.objects.filter(
        school_group=user_org,
        assigned_to__isnull=True,
        status='active'
    ).count()
    unread_total = sum(chat.unread_count for chat in chats if hasattr(chat, 'unread_count'))
    
    context = {
        'chats': chats,
        'status_filter': status_filter,
        'assigned_filter': assigned_filter,
        'unread_only': unread_only,
        'total_chats': total_chats,
        'unassigned_count': unassigned_count,
        'unread_total': unread_total,
        'user_org': user_org,
    }
    
    return render(request, 'chats/admin/inbox.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@admin_chat_access_required
def admin_chat_detail_view(request, chat_id):
    """Admin view of a specific chat."""
    chat = get_object_or_404(Chat, id=chat_id)
    user = request.user
    
    # Mark user messages as read when admin views
    chat.messages.filter(
        sender_type='user',
        is_read=False
    ).update(is_read=True)
    
    # Get all messages
    messages_list = chat.messages.all().order_by('created_at')
    
    context = {
        'chat': chat,
        'messages': messages_list,
        'form': ChatMessageForm(),
        'is_assigned': chat.assigned_to == user,
    }
    
    return render(request, 'chats/admin/chat_detail.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@admin_chat_access_required
@require_http_methods(['POST'])
def assign_chat_view(request, chat_id):
    """Admin assigns themselves to a chat."""
    chat = get_object_or_404(Chat, id=chat_id)
    user = request.user
    
    chat.assigned_to = user
    chat.save(update_fields=['assigned_to', 'updated_at'])
    
    messages.success(request, f'You have been assigned to this chat.')
    return redirect('chats:admin_chat_detail', chat_id=chat.id)


@login_required
@role_required(['admin', 'superadmin'])
@admin_chat_access_required
@require_http_methods(['POST'])
def unassign_chat_view(request, chat_id):
    """Admin unassigns themselves from a chat."""
    chat = get_object_or_404(Chat, id=chat_id)
    user = request.user
    
    if chat.assigned_to == user:
        chat.assigned_to = None
        chat.save(update_fields=['assigned_to', 'updated_at'])
        messages.success(request, 'You have been unassigned from this chat.')
    else:
        messages.error(request, 'You are not assigned to this chat.')
    
    return redirect('chats:admin_chat_detail', chat_id=chat.id)


@login_required
@role_required(['admin', 'superadmin'])
@admin_chat_access_required
@require_http_methods(['POST'])
def send_admin_message_view(request, chat_id):
    """Admin sends a message in a chat."""
    chat = get_object_or_404(Chat, id=chat_id)
    user = request.user
    
    # Verify chat is active or escalated
    if chat.status not in ['active', 'escalated']:
        messages.error(request, 'You cannot send messages to a closed chat.')
        return redirect('chats:admin_chat_detail', chat_id=chat.id)
    
    form = ChatMessageForm(request.POST)
    if form.is_valid():
        # Create admin message
        ChatMessage.objects.create(
            chat=chat,
            sender=user,
            sender_type='admin',
            content=form.cleaned_data['content'],
            is_read=False
        )
        
        # Update chat timestamp
        chat.save(update_fields=['updated_at'])
        
        messages.success(request, 'Message sent!')
    else:
        messages.error(request, 'Please correct the errors below.')
    
    return redirect('chats:admin_chat_detail', chat_id=chat.id)


@login_required
@role_required(['admin', 'superadmin'])
@admin_chat_access_required
@require_http_methods(['POST'])
def resolve_chat_view(request, chat_id):
    """Admin marks chat as resolved."""
    chat = get_object_or_404(Chat, id=chat_id)
    
    if not chat.can_resolve():
        messages.error(request, 'This chat cannot be resolved.')
        return redirect('chats:admin_chat_detail', chat_id=chat.id)
    
    chat.resolve()
    messages.success(request, 'Chat marked as resolved.')
    
    return redirect('chats:admin_chat_detail', chat_id=chat.id)


@login_required
@role_required(['admin', 'superadmin'])
@admin_chat_access_required
@require_http_methods(['POST'])
def close_chat_view(request, chat_id):
    """Admin closes a chat."""
    chat = get_object_or_404(Chat, id=chat_id)
    
    chat.close()
    messages.success(request, 'Chat closed.')
    
    return redirect('chats:admin_chat_detail', chat_id=chat.id)


@login_required
@role_required(['admin', 'superadmin'])
@admin_chat_access_required
def admin_poll_messages_view(request, chat_id):
    """Poll for new messages in a chat (AJAX endpoint for admin)."""
    chat = get_object_or_404(Chat, id=chat_id)
    user = request.user
    
    # Get last message ID from request
    last_message_id = request.GET.get('last_message_id', 0)
    try:
        last_message_id = int(last_message_id)
    except (ValueError, TypeError):
        last_message_id = 0
    
    # Get new messages
    if last_message_id > 0:
        new_messages = chat.messages.filter(
            id__gt=last_message_id
        ).order_by('created_at')
    else:
        new_messages = chat.messages.all().order_by('created_at')
    
    # Serialize messages
    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'sender_type': msg.sender_type,
            'sender_name': msg.sender.email if msg.sender else 'AI Assistant',
            'content': msg.content,
            'created_at': msg.created_at.isoformat(),
            'is_read': msg.is_read,
        })
    
    # Get unread count (user messages for admin)
    unread_count = chat.messages.filter(
        sender_type='user',
        is_read=False
    ).count()
    
    return JsonResponse({
        'messages': messages_data,
        'unread_count': unread_count,
        'chat_status': chat.status,
    })
