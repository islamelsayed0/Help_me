"""Admin inventory views (create, edit, delete)."""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q

from .models import InventoryItem
from .forms import InventoryItemForm
from .decorators import admin_inventory_access_required
from accounts.decorators import role_required
from accounts.utils import get_user_school_group


@login_required
@role_required(['admin', 'superadmin'])
def admin_item_list_view(request):
    """Admin list with create button, search, filter, low-stock count."""
    user_org = get_user_school_group(request.user)
    if user_org is None:
        messages.error(request, 'You must be in an organization to manage inventory.')
        return redirect('accounts:pending')

    if request.user.is_superadmin():
        items = InventoryItem.objects.all()
    else:
        items = InventoryItem.objects.filter(school_group=user_org)

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

    items = items.order_by('location', 'name')
    low_stock_count = sum(1 for i in items if i.is_low_stock)
    if request.user.is_superadmin():
        locations = InventoryItem.objects.values_list('location', flat=True).distinct().order_by('location')
    else:
        locations = InventoryItem.objects.filter(school_group=user_org).values_list('location', flat=True).distinct().order_by('location')

    context = {
        'items': items,
        'search_query': search,
        'location_filter': location_filter,
        'locations': locations,
        'total_count': items.count(),
        'low_stock_count': low_stock_count,
    }
    return render(request, 'inventory/admin/item_list.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@require_http_methods(['GET', 'POST'])
def admin_item_create_view(request):
    """Create a new inventory item."""
    user_org = get_user_school_group(request.user)
    if user_org is None:
        messages.error(request, 'You must be in an organization to add inventory.')
        return redirect('accounts:pending')

    if request.method == 'POST':
        form = InventoryItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.school_group = user_org
            item.save()
            messages.success(request, f'"{item.name}" added to inventory.')
            return redirect('inventory:admin_item_list')
    else:
        form = InventoryItemForm()

    context = {'form': form, 'is_edit': False}
    return render(request, 'inventory/admin/item_form.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@admin_inventory_access_required
@require_http_methods(['GET', 'POST'])
def admin_item_edit_view(request, item_id, **kwargs):
    """Edit an existing inventory item."""
    item = kwargs.get('item') or get_object_or_404(InventoryItem, id=item_id)

    if request.method == 'POST':
        form = InventoryItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, f'"{item.name}" updated.')
            return redirect('inventory:admin_item_list')
    else:
        form = InventoryItemForm(instance=item)

    context = {'form': form, 'item': item, 'is_edit': True}
    return render(request, 'inventory/admin/item_form.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@admin_inventory_access_required
@require_http_methods(['GET', 'POST'])
def admin_item_delete_view(request, item_id, **kwargs):
    """Confirm and delete an inventory item."""
    item = kwargs.get('item') or get_object_or_404(InventoryItem, id=item_id)

    if request.method == 'POST':
        name = item.name
        item.delete()
        messages.success(request, f'"{name}" removed from inventory.')
        return redirect('inventory:admin_item_list')

    context = {'item': item}
    return render(request, 'inventory/admin/item_confirm_delete.html', context)
