"""
Forms for knowledge base functionality.
"""
from django import forms
from .models import Article


class ArticleForm(forms.ModelForm):
    """Form for creating/editing articles."""
    class Meta:
        model = Article
        fields = ['title', 'content', 'category', 'tags', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
                'placeholder': 'Article title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
                'placeholder': 'Article content',
                'rows': 15
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
                'placeholder': 'Tags (comma-separated)'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['content'].required = True
        self.fields['tags'].help_text = 'Enter tags separated by commas (e.g., "tag1, tag2, tag3")'
    
    def clean_tags(self):
        """Convert comma-separated tags to JSON array."""
        tags_data = self.cleaned_data.get('tags', '')
        
        # If it's already a list (from JSONField), return it
        if isinstance(tags_data, list):
            return tags_data
        
        # If it's a string, parse it
        if isinstance(tags_data, str):
            if not tags_data.strip():
                return []
            # Split by comma, strip whitespace, filter empty
            tags = [tag.strip() for tag in tags_data.split(',') if tag.strip()]
            return tags
        
        # Default to empty list
        return []
    
    def clean_content(self):
        """Validate content."""
        content = self.cleaned_data.get('content', '').strip()
        if not content:
            raise forms.ValidationError('Content cannot be empty.')
        if len(content) < 50:
            raise forms.ValidationError('Content must be at least 50 characters.')
        return content
    
    def clean_title(self):
        """Validate title."""
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError('Title cannot be empty.')
        if len(title) < 5:
            raise forms.ValidationError('Title must be at least 5 characters.')
        return title
