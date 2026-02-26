"""User-facing inventory views (list and detail)."""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import InventoryItem
from .decorators import inventory_membership_required
from accounts.utils import get_user_school_group


@login_required
@inventory_membership_required
def item_list_view(request):
    """List all inventory items for the user's organization."""
    user_org = get_user_school_group(request.user)
    items = InventoryItem.objects.filter(school_group=user_org).order_by('location', 'name')

    search = request.GET.get('search', '').strip()
    if search:
        items = items.filter(
            Q(name__icontains=search) |
            Q(item_number__icontains=search) |
            Q(location__icontains=search) |
            Q(serial_number__icontains=search)
        )
    location_filter = request.GET.get('location', '').strip()
    if location_filter:
        items = items.filter(location__icontains=location_filter)

    locations = InventoryItem.objects.filter(school_group=user_org).values_list('location', flat=True).distinct().order_by('location')

    context = {
        'items': items,
        'search_query': search,
        'location_filter': location_filter,
        'locations': locations,
    }
    return render(request, 'inventory/item_list.html', context)


@login_required
@inventory_membership_required
def item_detail_view(request, item_id):
    """Detail view for one inventory item."""
    user_org = get_user_school_group(request.user)
    item = get_object_or_404(InventoryItem, id=item_id, school_group=user_org)
    context = {'item': item}
    return render(request, 'inventory/item_detail.html', context)
