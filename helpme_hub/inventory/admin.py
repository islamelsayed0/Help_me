from django.contrib import admin
from .models import InventoryItem


@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'item_number', 'quantity', 'min_stock', 'school_group', 'updated_at')
    list_filter = ('school_group',)
    search_fields = ('name', 'item_number', 'location', 'serial_number')
