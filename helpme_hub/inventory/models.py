from django.db import models
from schoolgroups.models import SchoolGroup


class InventoryItem(models.Model):
    """Organization-scoped inventory item with location, item number, serial, buy link, quantity."""
    school_group = models.ForeignKey(
        SchoolGroup,
        on_delete=models.CASCADE,
        related_name='inventory_items',
        help_text='Organization this item belongs to',
    )
    name = models.CharField(max_length=255, help_text='Display name (e.g. USB-C Hub)')
    location = models.CharField(max_length=255, help_text='Where it is stored (e.g. Closet A, Room 101)')
    item_number = models.CharField(max_length=100, help_text='SKU / part number')
    serial_number = models.CharField(max_length=255, blank=True, help_text='Optional serial number')
    buy_link = models.URLField(blank=True, help_text='Optional link to purchase / reorder')
    quantity = models.PositiveIntegerField(default=0, help_text='Quantity on hand')
    min_stock = models.PositiveIntegerField(default=0, help_text='Low-stock threshold; 0 = no alert')
    notes = models.TextField(blank=True, help_text='Optional notes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['location', 'name']
        verbose_name = 'Inventory item'
        verbose_name_plural = 'Inventory items'

    def __str__(self):
        return f'{self.name} ({self.item_number})'

    @property
    def is_low_stock(self):
        """True when min_stock > 0 and quantity <= min_stock."""
        return self.min_stock > 0 and self.quantity <= self.min_stock
