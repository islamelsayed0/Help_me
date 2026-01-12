from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def role_required(allowed_roles):
    """
    Decorator to check if user has required role.
    
    Usage:
        @role_required(['admin', 'superadmin'])
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect('accounts:login')
            
            if request.user.role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('accounts:dashboard')
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def superadmin_required(view_func):
    """
    Decorator to check if user is superadmin.
    
    Usage:
        @superadmin_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        if not request.user.is_superadmin():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('accounts:dashboard')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def membership_required(view_func):
    """
    Decorator to check if user has accepted membership in any school group.
    Redirects to pending page if no accepted membership.
    
    Usage:
        @membership_required
        def my_view(request):
            ...
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        # Check if user has accepted membership
        from schoolgroups.models import SchoolGroupMembership
        has_membership = SchoolGroupMembership.objects.filter(
            user=request.user,
            status='accepted'
        ).exists()
        
        if not has_membership:
            messages.info(request, 'You need to be a member of a school group to access this page.')
            return redirect('accounts:pending')
        
        return view_func(request, *args, **kwargs)
    return wrapper

