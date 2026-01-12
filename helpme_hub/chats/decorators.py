"""
Decorators for chat views to enforce permissions and organization isolation.
"""
from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Chat
from accounts.utils import get_user_school_group, has_accepted_membership


def chat_membership_required(view_func):
    """
    Decorator to ensure user has accepted membership in an organization.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if not has_accepted_membership(request.user):
            messages.info(request, 'You must be a member of an organization to access chats.')
            return redirect('accounts:pending')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def chat_owner_required(view_func):
    """
    Decorator to ensure user owns the chat they're trying to access.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        chat_id = kwargs.get('chat_id') or kwargs.get('pk')
        if chat_id:
            chat = get_object_or_404(Chat, id=chat_id)
            
            # Verify user owns the chat
            if chat.user != request.user:
                messages.error(request, 'You do not have permission to access this chat.')
                return redirect('chats:chat_list')
            
            # Verify organization membership
            user_org = get_user_school_group(request.user)
            if not user_org or user_org != chat.school_group:
                messages.error(request, 'You do not have permission to access this chat.')
                return redirect('chats:chat_list')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_chat_access_required(view_func):
    """
    Decorator to ensure admin can access chats from their organization.
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
        
        # Verify chat belongs to admin's organization
        chat_id = kwargs.get('chat_id') or kwargs.get('pk')
        if chat_id:
            chat = get_object_or_404(Chat, id=chat_id)
            user_org = get_user_school_group(request.user)
            
            if not user_org or user_org != chat.school_group:
                messages.error(request, 'You do not have permission to access this chat.')
                return redirect('chats:admin_inbox')
        
        return view_func(request, *args, **kwargs)
    return wrapper
