"""
Forms for ticket functionality.
"""
from django import forms
from .models import Ticket, TicketComment


class CreateTicketForm(forms.Form):
    """Form for creating a ticket directly."""
    title = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Enter ticket title',
        }),
        help_text='Brief title describing the issue'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Describe the issue in detail...',
            'rows': 5
        }),
        required=True,
        help_text='Detailed description of the issue'
    )
    priority = forms.ChoiceField(
        choices=Ticket.PRIORITY_CHOICES,
        initial='medium',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
        }),
        help_text='Priority level for this ticket'
    )


class EscalateChatForm(forms.Form):
    """Form for escalating a chat to a ticket."""
    title = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Enter ticket title',
        }),
        help_text='Brief title describing the issue'
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Describe the issue in detail...',
            'rows': 5
        }),
        required=True,
        help_text='Detailed description of the issue'
    )
    priority = forms.ChoiceField(
        choices=Ticket.PRIORITY_CHOICES,
        initial='medium',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
        }),
        help_text='Priority level for this ticket'
    )


class UpdateTicketStatusForm(forms.ModelForm):
    """Form for updating ticket status and priority."""
    class Meta:
        model = Ticket
        fields = ['status', 'priority']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            }),
        }


class ResolutionNotesForm(forms.Form):
    """Form for adding resolution notes to a ticket."""
    resolution_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Enter resolution notes...',
            'rows': 5
        }),
        required=True,
        help_text='Describe how the issue was resolved'
    )


class TicketCommentForm(forms.Form):
    """Form for adding a comment/update to a ticket."""
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Add a comment or update...',
            'rows': 3
        }),
        required=True,
        max_length=2000,
        help_text='Your comment or update'
    )


class AssignTicketForm(forms.Form):
    """Form for assigning a ticket to an admin."""
    assigned_to = forms.ModelChoiceField(
        queryset=None,  # Will be set in __init__
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
        }),
        help_text='Select an admin to assign this ticket to'
    )
    
    def __init__(self, *args, **kwargs):
        admins = kwargs.pop('admins', None)
        super().__init__(*args, **kwargs)
        if admins is not None:
            self.fields['assigned_to'].queryset = admins
