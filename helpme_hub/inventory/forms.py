from django import forms
from .models import InventoryItem


class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            'name', 'location', 'item_number', 'serial_number',
            'buy_link', 'quantity', 'min_stock', 'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark', 'placeholder': 'e.g. USB-C Hub'}),
            'location': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark', 'placeholder': 'e.g. Closet A'}),
            'item_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark', 'placeholder': 'SKU or part number'}),
            'serial_number': forms.TextInput(attrs={'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark', 'placeholder': 'Optional'}),
            'buy_link': forms.URLInput(attrs={'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark', 'placeholder': 'https://...'}),
            'quantity': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark', 'min': 0}),
            'min_stock': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark', 'min': 0}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark', 'rows': 3}),
        }
