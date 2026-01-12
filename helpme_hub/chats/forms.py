"""
Forms for chat functionality.
"""
from django import forms
from .models import Chat, ChatMessage


class CreateChatForm(forms.Form):
    """Form for creating a new chat."""
    initial_message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 text-base rounded-md bg-input-bg-light dark:bg-deep-dark border-2 border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-4 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-all',
            'placeholder': 'Example: "My printer won\'t print" or "The screen is black" or just leave blank and start typing after we begin...',
            'rows': 5
        }),
        required=False,
        help_text='Optional: Start the conversation with an initial message'
    )


class ChatMessageForm(forms.ModelForm):
    """Form for sending a chat message."""
    class Meta:
        model = ChatMessage
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 text-base rounded-md bg-input-bg-light dark:bg-deep-dark border-2 border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-4 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-all',
                'placeholder': 'Type your message here... Describe what\'s happening in simple words.',
                'rows': 4
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = True
        self.fields['content'].label = ''
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if not content:
            raise forms.ValidationError('Message cannot be empty.')
        if len(content) > 5000:
            raise forms.ValidationError('Message is too long. Maximum 5000 characters.')
        return content
