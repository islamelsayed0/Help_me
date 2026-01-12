"""
Decorators for knowledge base views to enforce permissions and organization isolation.
"""
from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Article
from accounts.utils import get_user_school_group, has_accepted_membership


def article_membership_required(view_func):
    """
    Decorator to ensure user has accepted membership in an organization.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if not has_accepted_membership(request.user):
            messages.info(request, 'You must be a member of an organization to access the knowledge base.')
            return redirect('accounts:pending')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_article_access_required(view_func):
    """
    Decorator to ensure admin can access articles from their organization.
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
        
        # Verify article belongs to admin's organization
        article_id = kwargs.get('article_id') or kwargs.get('pk')
        if article_id:
            article = get_object_or_404(Article, id=article_id)
            user_org = get_user_school_group(request.user)
            
            # Superadmins can access all articles
            if not request.user.is_superadmin():
                # Regular admins can only access articles from their organization
                if article.school_group and user_org != article.school_group:
                    messages.error(request, 'You do not have permission to access this article.')
                    return redirect('knowledge:admin_article_list')
        
        return view_func(request, *args, **kwargs)
    return wrapper
