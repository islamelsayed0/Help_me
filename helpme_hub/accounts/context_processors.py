"""
Context processors for the accounts app.
"""
from django.conf import settings


def google_oauth_enabled(request):
    """
    Add a context variable indicating if Google OAuth is enabled.
    This allows templates to conditionally show Google login buttons.
    """
    # #region agent log
    import json
    try:
        with open('/Users/islamelsayed/Documents/Help Me /.cursor/debug.log', 'a') as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "context_processors.py:google_oauth_enabled",
                "message": "Checking Google OAuth configuration",
                "data": {
                    "has_client_id": bool(getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', '')),
                    "has_client_secret": bool(getattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET', '')),
                    "providers_configured": 'google' in getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
                },
                "timestamp": int(__import__('time').time() * 1000)
            }
            f.write(json.dumps(log_entry) + '\n')
    except Exception:
        pass
    # #endregion
    
    client_id = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', '')
    client_secret = getattr(settings, 'GOOGLE_OAUTH2_CLIENT_SECRET', '')
    providers = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
    enabled = bool(client_id and client_secret and 'google' in providers)
    
    # #region agent log
    try:
        with open('/Users/islamelsayed/Documents/Help Me /.cursor/debug.log', 'a') as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run2",
                "hypothesisId": "D",
                "location": "context_processors.py:google_oauth_enabled",
                "message": "Initial enabled check",
                "data": {
                    "has_client_id": bool(client_id),
                    "has_client_secret": bool(client_secret),
                    "has_google_provider": 'google' in providers,
                    "enabled": enabled
                },
                "timestamp": int(__import__('time').time() * 1000)
            }
            f.write(json.dumps(log_entry) + '\n')
    except Exception:
        pass
    # #endregion
    
    # Get the Google OAuth login URL if enabled
    google_login_url = ''
    if enabled:
        try:
            from django.urls import reverse
            # #region agent log
            try:
                with open('/Users/islamelsayed/Documents/Help Me /.cursor/debug.log', 'a') as f:
                    log_entry = {
                        "sessionId": "debug-session",
                        "runId": "run2",
                        "hypothesisId": "C",
                        "location": "context_processors.py:google_oauth_enabled",
                        "message": "Attempting to reverse socialaccount_login URL",
                        "data": {"enabled": enabled},
                        "timestamp": int(__import__('time').time() * 1000)
                    }
                    f.write(json.dumps(log_entry) + '\n')
            except Exception:
                pass
            # #endregion
            google_login_url = reverse('google_login')
            # #region agent log
            try:
                with open('/Users/islamelsayed/Documents/Help Me /.cursor/debug.log', 'a') as f:
                    log_entry = {
                        "sessionId": "debug-session",
                        "runId": "run2",
                        "hypothesisId": "C",
                        "location": "context_processors.py:google_oauth_enabled",
                        "message": "Successfully reversed URL",
                        "data": {"url": google_login_url},
                        "timestamp": int(__import__('time').time() * 1000)
                    }
                    f.write(json.dumps(log_entry) + '\n')
            except Exception:
                pass
            # #endregion
        except Exception as e:
            # #region agent log
            try:
                with open('/Users/islamelsayed/Documents/Help Me /.cursor/debug.log', 'a') as f:
                    log_entry = {
                        "sessionId": "debug-session",
                        "runId": "run2",
                        "hypothesisId": "C",
                        "location": "context_processors.py:google_oauth_enabled",
                        "message": "Error reversing URL, disabling Google OAuth",
                        "data": {"error": str(e), "error_type": type(e).__name__},
                        "timestamp": int(__import__('time').time() * 1000)
                    }
                    f.write(json.dumps(log_entry) + '\n')
            except Exception:
                pass
            # #endregion
            # If URL reverse fails, disable Google OAuth
            enabled = False
            google_login_url = ''
    
    # #region agent log
    try:
        with open('/Users/islamelsayed/Documents/Help Me /.cursor/debug.log', 'a') as f:
            log_entry = {
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "context_processors.py:google_oauth_enabled",
                "message": "Google OAuth enabled status",
                "data": {"enabled": enabled, "has_url": bool(google_login_url)},
                "timestamp": int(__import__('time').time() * 1000)
            }
            f.write(json.dumps(log_entry) + '\n')
    except Exception:
        pass
    # #endregion
    
    return {
        'google_oauth_enabled': enabled,
        'google_login_url': google_login_url
    }

