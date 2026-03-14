"""
Context processors for the accounts app.
"""
from django.conf import settings


def google_oauth_enabled(request):
    """
    Add a context variable indicating if Google OAuth is enabled.
    This allows templates to conditionally show Google login buttons.
    """
    client_id = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', '')
    client_secret = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET', '')
    providers = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
    enabled = bool(client_id and client_secret and 'google' in providers)

    # Get the Google OAuth login URL if enabled
    google_login_url = ''
    if enabled:
        try:
            from django.urls import reverse
            google_login_url = reverse('google_login')
        except Exception as e:
            # If URL reverse fails, disable Google OAuth
            enabled = False
            google_login_url = ''

    return {
        'google_oauth_enabled': enabled,
        'google_login_url': google_login_url
    }

