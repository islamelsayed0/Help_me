"""Decorators for inventory views."""
from functools import wraps
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import InventoryItem
from accounts.utils import get_user_school_group, has_accepted_membership


def inventory_membership_required(view_func):
    """Require user to have accepted membership in an organization."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not has_accepted_membership(request.user):
            messages.info(request, 'You must be a member of an organization to view inventory.')
            return redirect('accounts:pending')
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_inventory_access_required(view_func):
    """Require admin role and optionally verify item belongs to user's org."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        if not request.user.is_admin() and not request.user.is_superadmin():
            messages.error(request, 'You must be an admin to access this page.')
            return redirect('inventory:item_list')
        if not has_accepted_membership(request.user):
            messages.info(request, 'You must be a member of an organization to manage inventory.')
            return redirect('accounts:pending')
        item_id = kwargs.get('item_id')
        if item_id:
            item = get_object_or_404(InventoryItem, id=item_id)
            user_org = get_user_school_group(request.user)
            if not request.user.is_superadmin() and item.school_group != user_org:
                messages.error(request, 'You do not have permission to access this item.')
                return redirect('inventory:admin_item_list')
            kwargs['item'] = item
        return view_func(request, *args, **kwargs)
    return wrapper
