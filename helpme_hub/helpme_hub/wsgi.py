"""
WSGI config for helpme_hub project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'helpme_hub.settings')

# Initialize Sentry before Django (if configured)
# Sentry will be initialized in settings.py if SENTRY_DSN is set

application = get_wsgi_application()


