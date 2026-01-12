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
    # #region agent log
    import json
    try:
        with open('/Users/islamelsayed/Documents/Help Me /.cursor/debug.log', 'a') as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run2",
                "hypothesisId": "B",
                "location": "accounts_tags.py:safe_provider_login_url",
                "message": "Checking provider availability",
                "data": {
                    "provider_id": provider_id,
                    "has_provider": provider_id in getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {}),
                    "providers_keys": list(getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {}).keys())
                },
                "timestamp": int(__import__('time').time() * 1000)
            }
            f.write(json.dumps(log_entry) + '\n')
    except Exception:
        pass
    # #endregion
    
    # Check if provider is configured in settings
    providers = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
    if provider_id not in providers:
        # #region agent log
        try:
            with open('/Users/islamelsayed/Documents/Help Me /.cursor/debug.log', 'a') as f:
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": "run2",
                    "hypothesisId": "B",
                    "location": "accounts_tags.py:safe_provider_login_url",
                    "message": "Provider not configured, returning empty",
                    "data": {"provider_id": provider_id},
                    "timestamp": int(__import__('time').time() * 1000)
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            pass
        # #endregion
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
            # #region agent log
            try:
                with open('/Users/islamelsayed/Documents/Help Me /.cursor/debug.log', 'a') as f:
                    log_entry = {
                        "sessionId": "debug-session",
                        "runId": "run2",
                        "hypothesisId": "B",
                        "location": "accounts_tags.py:safe_provider_login_url",
                        "message": "SocialApp does not exist in database",
                        "data": {"provider_id": provider_id},
                        "timestamp": int(__import__('time').time() * 1000)
                    }
                    f.write(json.dumps(log_entry) + '\n')
            except Exception:
                pass
            # #endregion
            return ''
        
        adapter = get_adapter(request)
        provider = adapter.get_provider(request, provider_id)
        url = reverse('socialaccount_login', args=[provider_id])
        # #region agent log
        try:
            with open('/Users/islamelsayed/Documents/Help Me /.cursor/debug.log', 'a') as f:
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": "run2",
                    "hypothesisId": "B",
                    "location": "accounts_tags.py:safe_provider_login_url",
                    "message": "Provider configured, got login URL",
                    "data": {"provider_id": provider_id, "url": url},
                    "timestamp": int(__import__('time').time() * 1000)
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            pass
        # #endregion
        return url
    except Exception as e:
        # #region agent log
        try:
            with open('/Users/islamelsayed/Documents/Help Me /.cursor/debug.log', 'a') as f:
                log_entry = {
                    "sessionId": "debug-session",
                    "runId": "run2",
                    "hypothesisId": "B",
                    "location": "accounts_tags.py:safe_provider_login_url",
                    "message": "Error getting provider URL",
                    "data": {"provider_id": provider_id, "error": str(e)},
                    "timestamp": int(__import__('time').time() * 1000)
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            pass
        # #endregion
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

