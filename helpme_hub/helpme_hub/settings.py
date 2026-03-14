"""
Django settings for helpme_hub project.

Generated for Phase 1: Foundation
"""

from pathlib import Path
import os
import sys
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    
    # Third party apps
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'whitenoise.runserver_nostatic',
    
    # Local apps
    'accounts',
    'schoolgroups',
    'chats',
    'tickets',
    'knowledge',
    'inventory',
    'audit',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # Required for django-allauth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'helpme_hub.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.google_oauth_enabled',
            ],
        },
    },
]

WSGI_APPLICATION = 'helpme_hub.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

# Set USE_SQLITE=1 in .env to use SQLite locally when Railway Postgres is unreachable.
# In production (DEBUG=False), DATABASE_URL must be set (e.g. by linking Postgres on Railway).
_db_url = config('DATABASE_URL', default='')
if config('USE_SQLITE', default=False, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif _db_url:
    DATABASES = {'default': dj_database_url.config(default=_db_url)}
else:
    # Fallback to SQLite only for local dev (DEBUG=True); production must set DATABASE_URL.
    if not config('DEBUG', default=True, cast=bool):
        raise ValueError(
            'DATABASE_URL must be set in production. Link your Postgres service to this service in Railway, '
            'or set DATABASE_URL in the service Variables.'
        )
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    {
        'NAME': 'accounts.validators.UppercaseValidator',
    },
    {
        'NAME': 'accounts.validators.SymbolValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = config('STATIC_URL', default='/static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = BASE_DIR / 'media'

# WhiteNoise configuration
# Use ManifestStaticFilesStorage for production, but not for tests
if DEBUG and 'test' not in sys.argv:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django Allauth Configuration
SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Allauth Settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Can be changed to 'mandatory' later
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = False
ACCOUNT_SESSION_REMEMBER = True
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Google OAuth Settings
# Get Google OAuth credentials from environment variables
GOOGLE_OAUTH2_CLIENT_ID = config('GOOGLE_OAUTH2_CLIENT_ID', default='')
GOOGLE_OAUTH2_CLIENT_SECRET = config('GOOGLE_OAUTH2_CLIENT_SECRET', default='')

# Validate Google OAuth credentials (only in DEBUG mode to avoid production issues)
if DEBUG:
    if not GOOGLE_OAUTH2_CLIENT_ID or not GOOGLE_OAUTH2_CLIENT_SECRET:
        import warnings
        warnings.warn(
            'Google OAuth credentials are not set. Please set GOOGLE_OAUTH2_CLIENT_ID and '
            'GOOGLE_OAUTH2_CLIENT_SECRET in your .env file. Google OAuth will not work until these are configured.',
            UserWarning
        )

# Configure Google OAuth provider
# Only include Google provider if credentials are set
if GOOGLE_OAUTH2_CLIENT_ID and GOOGLE_OAUTH2_CLIENT_SECRET:
    SOCIALACCOUNT_PROVIDERS = {
        'google': {
            'SCOPE': [
                'profile',
                'email',
            ],
            'AUTH_PARAMS': {
                'access_type': 'online',
            },
            'APP': {
                'client_id': GOOGLE_OAUTH2_CLIENT_ID,
                'secret': GOOGLE_OAUTH2_CLIENT_SECRET,
            }
        }
    }
else:
    # Empty providers dict if credentials are missing
    # This prevents errors but Google OAuth won't work
    SOCIALACCOUNT_PROVIDERS = {}

# Google Gemini AI Settings
GOOGLE_GEMINI_API_KEY = config('GOOGLE_GEMINI_API_KEY', default='')
GEMINI_MODEL = config('GEMINI_MODEL', default='gemini-2.0-flash')  # Use gemini-2.0-flash (available model)
GEMINI_MAX_TOKENS = config('GEMINI_MAX_TOKENS', default=300, cast=int)
GEMINI_TEMPERATURE = config('GEMINI_TEMPERATURE', default=0.7, cast=float)

# Stripe Settings
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')
STRIPE_PRICE_ID_PRO_MONTHLY = config('STRIPE_PRICE_ID_PRO_MONTHLY', default='')
STRIPE_PRICE_ID_PRO_YEARLY = config('STRIPE_PRICE_ID_PRO_YEARLY', default='')
STRIPE_PRICE_ID_ENTERPRISE = config('STRIPE_PRICE_ID_ENTERPRISE', default='')
STRIPE_PRICE_ID_AI_ADDON = config('STRIPE_PRICE_ID_AI_ADDON', default='')

# Donation link (Support page). Optional; leave empty to hide Donate button.
DONATION_URL = config('DONATION_URL', default='https://buy.stripe.com/5kQ28qa9sewa60N24s4ZG00')

SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'

# Email Configuration
# For local development, use console backend (emails printed to console)
# For production, configure SMTP settings in .env file
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=25, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=False, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='webmaster@localhost')

# Security Settings
# Production security settings - automatically enabled when DEBUG=False
if not DEBUG:
    # Force HTTPS
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # Security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_REFERRER_POLICY = 'same-origin'
    
    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Proxy settings (for Railway/Heroku)
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

# Logging Configuration
# In production (e.g. Railway), use only console so we don't rely on writable filesystem
_log_handlers = ['console']
if DEBUG:
    _log_handlers = ['console', 'file']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': _log_handlers,
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': _log_handlers,
            'level': 'ERROR',
            'propagate': False,
        },
        'accounts': {
            'handlers': _log_handlers,
            'level': 'INFO',
            'propagate': False,
        },
        'tickets': {
            'handlers': _log_handlers,
            'level': 'INFO',
            'propagate': False,
        },
        'chats': {
            'handlers': _log_handlers,
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist (moved to end to avoid import issues)
try:
    import os
    logs_dir = BASE_DIR / 'logs'
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
except Exception:
    pass  # Ignore errors during settings import

# Session Settings
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Sentry Error Monitoring (Optional)
# Get your DSN from https://sentry.io/settings/projects/
SENTRY_DSN = config('SENTRY_DSN', default='')
SENTRY_ENVIRONMENT = config('SENTRY_ENVIRONMENT', default='development' if DEBUG else 'production')
SENTRY_TRACES_SAMPLE_RATE = config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float)  # 10% of transactions

if SENTRY_DSN and not DEBUG:  # Only enable Sentry in production
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration
    
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        environment=SENTRY_ENVIRONMENT,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
                cache_spans=True,
            ),
            LoggingIntegration(
                level=None,  # Capture all logs
                event_level=None,  # Send all log events
            ),
        ],
        # Performance monitoring
        traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=0.0,  # Disable profiling by default
        
        # Send user info with errors
        send_default_pii=True,
        
        # Release tracking (optional)
        # release="helpme-hub@1.0.0",
    )