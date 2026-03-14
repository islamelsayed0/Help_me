"""
User-facing chat views.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count, Max
import json

from .models import Chat, ChatMessage
from .forms import CreateChatForm, ChatMessageForm
from .decorators import chat_membership_required, chat_owner_required
from .ai_service import generate_ai_response, process_ai_response, detect_ticket_intent
from accounts.utils import get_user_school_group, has_accepted_membership
from audit.utils import log_action
from tickets.services import create_ticket_from_chat


@login_required
@chat_membership_required
def chat_list_view(request):
    """List all chats for the current user."""
    user = request.user
    user_org = get_user_school_group(user)
    
    # Get user's chats from their current organization
    chats = Chat.objects.filter(
        user=user,
        school_group=user_org
    ).annotate(
        last_message_time=Max('messages__created_at'),
        unread_count=Count('messages', filter=Q(
            messages__sender_type__in=['admin', 'ai'],
            messages__is_read=False
        ))
    ).order_by('-updated_at', '-created_at')
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['active', 'escalated', 'resolved', 'closed']:
        chats = chats.filter(status=status_filter)
    
    context = {
        'chats': chats,
        'status_filter': status_filter,
        'user_org': user_org,
    }
    
    return render(request, 'chats/chat_list.html', context)


@login_required
@chat_membership_required
@chat_owner_required
def chat_detail_view(request, chat_id):
    """Display chat messages and handle new messages."""
    chat = get_object_or_404(Chat, id=chat_id)
    user = request.user
    
    # Mark messages as read when viewing
    chat.mark_all_read(user)
    
    # Get all messages
    messages_list = chat.messages.all().order_by('created_at')
    
    context = {
        'chat': chat,
        'messages': messages_list,
        'form': ChatMessageForm(),
    }
    
    return render(request, 'chats/chat_detail.html', context)


@login_required
@chat_membership_required
@require_http_methods(['GET', 'POST'])
def create_chat_view(request):
    """Create a new chat."""
    user = request.user
    user_org = get_user_school_group(user)
    
    if request.method == 'POST':
        form = CreateChatForm(request.POST)
        if form.is_valid():
            # Create chat
            chat = Chat.objects.create(
                user=user,
                school_group=user_org,
                status='active'
            )
            
            # Add welcome message from AI or system
            welcome_message = "Hi! 👋 I'm here to help you. Please describe what's happening with your device or what problem you're experiencing. Don't worry - just tell me in simple words and I'll help you figure it out!"
            
            # Create welcome message
            ChatMessage.objects.create(
                chat=chat,
                sender=None,
                sender_type='ai',
                content=welcome_message,
                is_read=False
            )
            
            # Create initial message if provided
            initial_message = form.cleaned_data.get('initial_message', '').strip()
            if initial_message:
                ChatMessage.objects.create(
                    chat=chat,
                    sender=user,
                    sender_type='user',
                    content=initial_message,
                    is_read=False
                )
                
                # Trigger AI response for all users with an organization
                if user_org:
                    try:
                        ai_message = process_ai_response(chat.id, initial_message)
                        if not ai_message:
                            # AI failed silently - log but don't show error to user
                            import logging
                            logging.getLogger(__name__).warning(f'AI response failed for chat {chat.id} - may be quota/billing issue')
                    except Exception as e:
                        # Log error but don't fail chat creation
                        import logging
                        error_str = str(e)
                        if 'quota' in error_str.lower() or 'billing' in error_str.lower() or '429' in error_str:
                            logging.getLogger(__name__).warning(f'AI quota/billing limit reached for chat {chat.id}')
                        else:
                            logging.getLogger(__name__).error(f'AI response failed: {error_str}')
            
            messages.success(request, 'Chat created successfully!')
            return redirect('chats:chat_detail', chat_id=chat.id)
    else:
        form = CreateChatForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'chats/create_chat.html', context)


@login_required
@chat_membership_required
@chat_owner_required
@require_http_methods(['POST'])
def send_message_view(request, chat_id):
    """Send a message in a chat."""
    chat = get_object_or_404(Chat, id=chat_id)
    user = request.user
    
    # Verify chat is active
    if chat.status != 'active':
        messages.error(request, 'You cannot send messages to a closed chat.')
        return redirect('chats:chat_detail', chat_id=chat.id)
    
    form = ChatMessageForm(request.POST)
    if form.is_valid():
        content = form.cleaned_data['content']

        # Create user message
        user_message = ChatMessage.objects.create(
            chat=chat,
            sender=user,
            sender_type='user',
            content=content,
            is_read=False
        )
        
        # Update chat timestamp
        chat.save(update_fields=['updated_at'])
        
        # If the user used the /ticket command or expressed a clear ticket intent,
        # open a ticket from this chat instead of sending the message to the AI.
        text = content.strip()
        text_lower = text.lower()
        intent = detect_ticket_intent(text)

        if text.startswith('/ticket'):
            ticket = _create_ticket_from_chat_command(user, chat, text)
            if ticket:
                ChatMessage.objects.create(
                    chat=chat,
                    sender=None,
                    sender_type='ai',
                    content=(
                        f"I've opened Ticket #{ticket.id} for you: \"{ticket.title}\". "
                        "An admin will review it and follow up."
                    ),
                    is_read=False,
                )
        elif intent and intent.get('intent') == 'create_ticket':
            # Let the intent helper provide a category hint while reusing the
            # same /ticket parsing behaviour for consistency.
            hinted_category = intent.get('category') or 'general'
            synthetic_command = f"/ticket {hinted_category} {text}"
            ticket = _create_ticket_from_chat_command(user, chat, synthetic_command)
            if ticket:
                ChatMessage.objects.create(
                    chat=chat,
                    sender=None,
                    sender_type='ai',
                    content=(
                        f"I've opened Ticket #{ticket.id} for you: \"{ticket.title}\". "
                        "An admin will review it and follow up."
                    ),
                    is_read=False,
                )
        else:
            # Trigger AI response for all users with an organization
            user_org = get_user_school_group(user)
            if user_org:
                try:
                    process_ai_response(chat.id, content)
                except Exception as e:
                    # Log error but don't fail message sending
                    import logging
                    logging.getLogger(__name__).error(f'AI response failed: {str(e)}')
        
        messages.success(request, 'Message sent!')
    else:
        messages.error(request, 'Please correct the errors below.')
    
    return redirect('chats:chat_detail', chat_id=chat.id)


def _create_ticket_from_chat_command(user, chat, command_text):
    """
    Parse a /ticket command sent in chat and create a linked Ticket.
    
    Supported formats:
        /ticket printer Optional extra description...
        /ticket account ...
        /ticket device ...
        /ticket           (uses generic title)
    """
    # Only allow ticket creation for active chats that can escalate
    if not chat.can_escalate():
        return None
    if hasattr(chat, 'ticket') and chat.ticket:
        return chat.ticket

    text = command_text.strip()
    parts = text.split(None, 2)  # /ticket <category> <rest>

    category = 'general'
    if len(parts) >= 2:
        candidate = parts[1].lower()
        if candidate in ['printer', 'print']:
            category = 'printer'
        elif candidate in ['account', 'login', 'password']:
            category = 'account'
        elif candidate in ['device', 'promethean', 'board', 'screen']:
            category = 'device'

    extra_details = ''
    if len(parts) == 3:
        extra_details = parts[2].strip()

    ticket = create_ticket_from_chat(
        user=user,
        school_group=chat.school_group,
        chat=chat,
        data={
            'category': category,
            'extra_details': extra_details,
        },
    )

    # Optionally log the action for auditing
    try:
        log_action(
            user,
            'ticket_created_from_chat_command',
            'Ticket',
            ticket.id,
            chat.school_group,
            f'Ticket \"{ticket.title}\" created from /ticket command in Chat #{chat.id}',
        )
    except Exception:
        # Logging errors should never break the user flow
        pass

    return ticket


@login_required
@chat_membership_required
@chat_owner_required
@require_http_methods(['GET', 'POST'])
def escalate_chat_view(request, chat_id):
    """Escalate chat to ticket."""
    chat = get_object_or_404(Chat, id=chat_id)
    user = request.user
    
    # Check if chat is already escalated
    if hasattr(chat, 'ticket') and chat.ticket:
        messages.info(request, 'This chat has already been escalated to a ticket.')
        return redirect('tickets:ticket_detail', ticket_id=chat.ticket.id)
    
    if not chat.can_escalate():
        messages.error(request, 'This chat cannot be escalated.')
        return redirect('chats:chat_detail', chat_id=chat.id)
    
    from tickets.forms import EscalateChatForm
    from tickets.models import Ticket
    from tickets.services import create_ticket_from_chat
    
    if request.method == 'POST':
        form = EscalateChatForm(request.POST)
        if form.is_valid():
            # Create ticket from chat using shared service helper so all
            # chat‑created tickets are consistent and tagged as chat‑sourced.
            ticket = create_ticket_from_chat(
                user=user,
                school_group=chat.school_group,
                chat=chat,
                data={
                    'short_title': form.cleaned_data['title'],
                    'full_description': form.cleaned_data['description'],
                    'priority': form.cleaned_data['priority'],
                },
            )
            
            # Send email notification
            try:
                from accounts.notifications import send_chat_escalated_email
                send_chat_escalated_email(chat, ticket)
            except Exception as e:
                logger.error(f'Failed to send chat escalated email: {str(e)}')
            
            messages.success(request, 'Chat escalated to ticket successfully!')
            return redirect('tickets:ticket_detail', ticket_id=ticket.id)
    else:
        # Pre-fill form with chat context
        initial_data = {
            'title': f'Support Request from Chat #{chat.id}',
            'description': f'This ticket was escalated from Chat #{chat.id}.\n\nChat messages:\n' + '\n'.join([
                f"{msg.sender.email if msg.sender else 'AI'}: {msg.content[:100]}"
                for msg in chat.messages.all()[:5]
            ]),
            'priority': 'medium'
        }
        form = EscalateChatForm(initial=initial_data)
    
    context = {
        'chat': chat,
        'form': form,
    }
    
    return render(request, 'chats/escalate_chat.html', context)


@login_required
@chat_membership_required
@require_http_methods(['POST'])
def mark_messages_read_view(request, chat_id):
    """Mark all messages as read in a chat."""
    chat = get_object_or_404(Chat, id=chat_id)
    user = request.user
    
    # Verify user has access
    if chat.user != user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    chat.mark_all_read(user)
    
    return JsonResponse({'success': True})


@login_required
@chat_membership_required
def poll_messages_view(request, chat_id):
    """Poll for new messages in a chat (AJAX endpoint)."""
    chat = get_object_or_404(Chat, id=chat_id)
    user = request.user
    
    # Verify user has access
    if chat.user != user:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
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
    
    # Get unread count
    unread_count = chat.get_unread_count(user)
    
    return JsonResponse({
        'messages': messages_data,
        'unread_count': unread_count,
        'chat_status': chat.status,
    })


@login_required
@chat_membership_required
@require_http_methods(['POST'])
def quick_help_view(request):
    """Quick AI help endpoint for the floating help bubble."""
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        history = data.get('history', [])
        
        if not user_message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        # Get user's organization (AI is available to all users with an organization)
        user_org = get_user_school_group(request.user)
        if not user_org:
            return JsonResponse({
                'response': 'You need to be in an organization to use AI assistance.'
            })
        
        # Generate AI response
        ai_response = generate_ai_response(
            chat_id=None,  # Not associated with a specific chat
            user_message=user_message,
            conversation_history=history
        )
        
        if ai_response:
            return JsonResponse({'response': ai_response})
        else:
            # Check if it's a quota/billing issue by checking logs or API response
            # For now, provide a helpful error message
            return JsonResponse({
                'response': 'Sorry, I\'m unable to respond right now. This may be due to API quota limits. Please contact your administrator to check the Google Cloud billing settings for the AI service.'
            })
            
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f'Quick help error: {str(e)}')
        return JsonResponse({
            'response': 'Sorry, I encountered an error. Please try again.'
        }, status=500)
