from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from schoolgroups.models import SchoolGroup, JoinRequest, SchoolGroupMembership


def generate_username_from_email(email):
    """
    Generate a username from email address.
    - Extract part before @
    - Remove special characters except dots, underscores, hyphens
    - Replace dots with underscores for cleaner usernames
    - Handle duplicates by appending numbers
    - Truncate to Django's username max length (150 chars)
    """
    # Extract part before @
    base_username = email.split('@')[0]
    
    # Clean: keep alphanumeric, dots, underscores, hyphens
    base_username = ''.join(c for c in base_username if c.isalnum() or c in '._-')
    
    # Replace dots with underscores for cleaner usernames
    base_username = base_username.replace('.', '_')
    
    # Replace hyphens with underscores for consistency
    base_username = base_username.replace('-', '_')
    
    # Remove multiple consecutive underscores
    while '__' in base_username:
        base_username = base_username.replace('__', '_')
    
    # Remove leading/trailing underscores
    base_username = base_username.strip('_')
    
    # If empty after cleaning, use a default
    if not base_username:
        base_username = 'user'
    
    # Truncate to Django's username max length (150 chars), leaving room for counter
    max_base_length = 140  # Leave room for counter (e.g., "_123")
    if len(base_username) > max_base_length:
        base_username = base_username[:max_base_length]
    
    # Check for duplicates and append number if needed
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        # Append counter, ensuring total length doesn't exceed 150
        counter_str = str(counter)
        max_length_with_counter = 150 - len(counter_str)
        if len(base_username) > max_length_with_counter:
            base_username = base_username[:max_length_with_counter]
        username = f"{base_username}{counter_str}"
        counter += 1
        # Safety check to prevent infinite loop
        if counter > 10000:
            break
    
    return username


class UserRegistrationForm(UserCreationForm):
    """Registration form for new users."""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Email address'
        })
    )
    first_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'First name'
        })
    )
    last_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Last name'
        })
    )
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field from form since it will be auto-generated
        if 'username' in self.fields:
            del self.fields['username']
        
        # Ensure email field is required
        if 'email' in self.fields:
            self.fields['email'].required = True
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Confirm password'
        })
    
    def clean_email(self):
        """Validate email uniqueness."""
        email = self.cleaned_data.get('email', '').lower().strip()
        if email:
            # Check if email already exists (exclude current user if editing)
            if self.instance and self.instance.pk:
                existing_user = User.objects.filter(email=email).exclude(pk=self.instance.pk).first()
            else:
                existing_user = User.objects.filter(email=email).first()
            
            if existing_user:
                raise forms.ValidationError('A user with this email address already exists.')
        
        return email
    
    def save(self, commit=True):
        import logging
        logger = logging.getLogger(__name__)
        
        user = super().save(commit=False)
        # Email is already normalized and validated in clean_email()
        user.email = self.cleaned_data.get('email', '').lower().strip()
        
        # Auto-generate username from email
        if not user.username:
            base_username = generate_username_from_email(user.email)
            username = base_username
            
            # Handle username conflicts
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                if counter > 1000:  # Safety limit
                    raise ValueError('Unable to generate unique username after multiple attempts')
            
            user.username = username
            logger.info(f'Generated username for {user.email}: {username}')
        
        if commit:
            try:
                user.save()
                logger.info(f'User saved successfully: {user.email} (ID: {user.id}, username: {user.username})')
            except Exception as e:
                logger.error(f'Error saving user {user.email}: {str(e)}', exc_info=True)
                raise
        
        return user


class JoinRequestForm(forms.Form):
    """Form for requesting to join an organization using an access code."""
    access_code = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Enter access code',
            'autocomplete': 'off'
        }),
        help_text='Enter the access code provided by the organization administrator'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_access_code(self):
        """Validate access code and find the organization."""
        access_code_input = self.cleaned_data.get('access_code', '').strip()
        
        if not access_code_input:
            raise forms.ValidationError('Please enter an access code.')
        
        if not self.user:
            raise forms.ValidationError('User must be authenticated to request membership.')
        
        # Normalize the access code (remove dashes, uppercase)
        access_code = SchoolGroup.normalize_access_code(access_code_input)
        
        # Find organization by access code
        try:
            school_group = SchoolGroup.objects.get(access_code=access_code)
        except SchoolGroup.DoesNotExist:
            raise forms.ValidationError('Invalid access code. Please check the code and try again.')
        
        # Check if code is valid (not expired)
        if not school_group.is_access_code_valid():
            raise forms.ValidationError('This access code has expired. Please contact the organization administrator for a new code.')
        
        # Check if organization is active
        if not school_group.is_active:
            raise forms.ValidationError('This organization is not currently accepting new members.')
        
        # Check if user already has a membership (any status)
        if SchoolGroupMembership.objects.filter(
            user=self.user,
            school_group=school_group
        ).exists():
            raise forms.ValidationError('You already have a membership request or membership for this organization.')
        
        # Check if user already has a pending request
        if JoinRequest.objects.filter(
            user=self.user,
            school_group=school_group,
            status='pending'
        ).exists():
            raise forms.ValidationError('You already have a pending request for this organization.')
        
        # Store the school_group in cleaned_data for use in view
        self.cleaned_data['school_group'] = school_group
        
        return access_code


class CreateOrganizationForm(forms.Form):
    """Form for creating a new organization."""
    name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Organization name'
        }),
        help_text='Enter a unique name for your organization'
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-2 rounded-md bg-input-bg-light dark:bg-deep-dark border border-[rgba(15,23,42,0.14)] dark:border-[rgba(148,163,184,0.25)] text-text-primary-light dark:text-text-primary-dark placeholder:text-text-muted-light dark:placeholder:text-text-muted-dark focus:outline-none focus:ring-2 focus:ring-light-blue-focus dark:focus:ring-calm-blue-focus transition-colors',
            'placeholder': 'Organization description (optional)',
            'rows': 4
        }),
        help_text='Optional description of your organization'
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        """Validate organization name is unique."""
        name = self.cleaned_data.get('name')
        
        if not name:
            return name
        
        if SchoolGroup.objects.filter(name=name).exists():
            raise forms.ValidationError('An organization with this name already exists. Please choose a different name.')
        
        return name
    
    def clean(self):
        """Validate that user hasn't already created an organization."""
        cleaned_data = super().clean()
        
        if not self.user:
            raise forms.ValidationError('User must be authenticated to create an organization.')
        
        if self.user.has_created_organization():
            raise forms.ValidationError('You have already created an organization. Each user can only create one organization.')
        
        return cleaned_data

