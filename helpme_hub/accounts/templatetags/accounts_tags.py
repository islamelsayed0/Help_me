"""
Custom template tags for the accounts app.
"""
from django import template
from django.conf import settings
from django.urls import reverse
from accounts.utils import get_user_organizations

register = template.Library()


@register.simple_tag(takes_context=True)
def safe_provider_login_url(context, provider_id):
    """
    Safely get the provider login URL only if the provider is configured.
    Returns empty string if provider is not configured to avoid DoesNotExist errors.
    """
    # Check if provider is configured in settings
    providers = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
    if provider_id not in providers:
        return ''
    
    # Provider is configured, try to get the login URL
    try:
        from allauth.socialaccount.adapter import get_adapter
        from allauth.socialaccount.models import SocialApp
        request = context.get('request')
        
        # Check if SocialApp exists in database (required by django-allauth)
        # Even with APP config in settings, allauth may require a DB record
        try:
            SocialApp.objects.get(provider=provider_id)
        except SocialApp.DoesNotExist:
            return ''
        
        adapter = get_adapter(request)
        provider = adapter.get_provider(request, provider_id)
        url = reverse('socialaccount_login', args=[provider_id])
        return url
    except Exception:
        return ''


@register.simple_tag
def get_user_organizations_tag(user):
    """
    Get all organizations user is a member of.
    Returns list of SchoolGroup objects.
    """
    if not user or not user.is_authenticated:
        return []
    return list(get_user_organizations(user))

