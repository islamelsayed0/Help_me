"""
Django settings for helpme_hub project.

Generated for Phase 1: Foundation
"""

from pathlib import Path
import json
import os
import sys
import time
from urllib.parse import quote_plus, urlparse

import dj_database_url
import environ
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
if os.environ.get('RAILWAY_ENVIRONMENT', '') == 'production':
    DEBUG = False

IS_PRODUCTION = (not DEBUG) or (os.environ.get('RAILWAY_ENVIRONMENT', '') == 'production')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str('SECRET_KEY', default='').strip()
if IS_PRODUCTION and not SECRET_KEY:
    raise ImproperlyConfigured(
        'SECRET_KEY must be set via environment variable in production.'
    )
if not SECRET_KEY:
    SECRET_KEY = 'django-insecure-dev-only-not-for-production'

_allowed = env.str('ALLOWED_HOSTS', default='localhost,127.0.0.1,.up.railway.app')
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]
if '*' in ALLOWED_HOSTS and IS_PRODUCTION:
    raise ImproperlyConfigured('ALLOWED_HOSTS cannot be "*" in production.')

_csrf_origins = env.str('CSRF_TRUSTED_ORIGINS', default='')
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_origins.split(',') if o.strip()]


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

# Set USE_SQLITE=True in .env for local SQLite. Production must use DATABASE_URL from Railway (or similar).


def _database_url_from_pg_env():
    """Build postgres URL from PG* vars (e.g. Railway/Heroku-style split credentials)."""
    host = os.environ.get('PGHOST', '').strip()
    port = os.environ.get('PGPORT', '').strip() or '5432'
    user = os.environ.get('PGUSER', '').strip()
    password = os.environ.get('PGPASSWORD', '')
    name = os.environ.get('PGDATABASE', '').strip()
    if not (host and user and name):
        return ''
    return (
        f'postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{name}'
    )


def _database_url_has_hostname(url):
    """True when URL has a TCP host (not socket-only postgresql:///db)."""
    if not url:
        return False
    norm = url.replace('postgres://', 'postgresql://', 1).split('?', 1)[0]
    return bool(urlparse(norm).hostname)


def _resolve_database_url():
    """Prefer DATABASE_URL / DATABASE_PRIVATE_URL if they include a host; else PG* composite."""
    direct = env.str('DATABASE_URL', default='').strip() or env.str(
        'DATABASE_PRIVATE_URL', default=''
    ).strip()
    built = _database_url_from_pg_env()
    if direct and _database_url_has_hostname(direct):
        return direct, 'env_url'
    # Socket-only or broken DATABASE_URL is common; Railway still exposes PGHOST, etc.
    if built:
        if direct and not _database_url_has_hostname(direct):
            return built, 'pg_env_fallback'
        return built, 'pg_env'
    if direct:
        return direct, 'env_url'
    return '', 'none'


_db_url, _db_url_source = _resolve_database_url()
USE_SQLITE = env.bool('USE_SQLITE', default=False)

# region agent log
def _agent_log_db(hypothesis_id, message, data):
    payload = {
        'sessionId': '51bc6f',
        'hypothesisId': hypothesis_id,
        'location': 'helpme_hub/settings.py:database',
        'message': message,
        'data': data,
        'timestamp': int(time.time() * 1000),
    }
    try:
        log_path = BASE_DIR.parent / '.cursor' / 'debug-51bc6f.log'
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(payload) + '\n')
    except Exception:
        pass


_agent_log_db(
    'H1',
    'db_url_resolution',
    {
        'is_production': IS_PRODUCTION,
        'use_sqlite': USE_SQLITE,
        'db_url_source': _db_url_source,
        'has_nonempty_db_url': bool(_db_url),
        'has_DATABASE_URL': bool(os.environ.get('DATABASE_URL', '').strip()),
        'has_DATABASE_PRIVATE_URL': bool(os.environ.get('DATABASE_PRIVATE_URL', '').strip()),
        'has_PGHOST': bool(os.environ.get('PGHOST', '').strip()),
        'has_PGDATABASE': bool(os.environ.get('PGDATABASE', '').strip()),
    },
)
# endregion

if IS_PRODUCTION:
    if USE_SQLITE:
        raise ImproperlyConfigured('USE_SQLITE must not be enabled in production.')
    if not _db_url:
        # region agent log
        diag = {
            'has_DATABASE_URL': bool(os.environ.get('DATABASE_URL', '').strip()),
            'has_DATABASE_PRIVATE_URL': bool(os.environ.get('DATABASE_PRIVATE_URL', '').strip()),
            'has_PGHOST': bool(os.environ.get('PGHOST', '').strip()),
            'has_PGUSER': bool(os.environ.get('PGUSER', '').strip()),
            'has_PGDATABASE': bool(os.environ.get('PGDATABASE', '').strip()),
            'has_PGPASSWORD': bool(os.environ.get('PGPASSWORD', '').strip()),
        }
        _agent_log_db('H2', 'production_missing_db_url', diag)
        # One-shot stderr (Django may load settings more than once per process)
        if not os.environ.get('__HELPME_DB_DIAG_STDERR__'):
            os.environ['__HELPME_DB_DIAG_STDERR__'] = '1'
            sys.stderr.write('DJANGO_DB_DIAG ' + json.dumps(diag) + '\n')
        # endregion
        raise ImproperlyConfigured(
            'DATABASE_URL or DATABASE_PRIVATE_URL is required in production. '
            'On Railway: add a PostgreSQL service and reference DATABASE_URL (or PGHOST/PGUSER/'
            'PGPASSWORD/PGDATABASE) on this service.'
        )
    # Host-less URLs make libpq use a Unix socket inside the container (fails on Railway).
    if not _database_url_has_hostname(_db_url):
        raise ImproperlyConfigured(
            'DATABASE_URL must include a database host (e.g. …@postgres.railway.internal:5432/railway), '
            'or set PGHOST, PGUSER, PGPASSWORD, and PGDATABASE on this service. '
            'Socket-only URLs like postgresql:///dbname do not work on Railway. '
            'Copy the full DATABASE_URL from your Railway Postgres service Variables tab, '
            'or reference those PG* variables from Postgres onto the web service.'
        )
    DATABASES = {'default': dj_database_url.config(default=_db_url)}
elif USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif _db_url:
    DATABASES = {'default': dj_database_url.config(default=_db_url)}
else:
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

STATIC_URL = env.str('STATIC_URL', default='/static/')
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = env.str('MEDIA_URL', default='/media/')
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
if DEBUG:
    ACCOUNT_EMAIL_VERIFICATION = 'none'
else:
    ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SIGNUP_EMAIL_ENTER_TWICE = False
ACCOUNT_SESSION_REMEMBER = True
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Google OAuth Settings
# Get Google OAuth credentials from environment variables
GOOGLE_OAUTH2_CLIENT_ID = env.str('GOOGLE_OAUTH2_CLIENT_ID', default='')
GOOGLE_OAUTH2_CLIENT_SECRET = env.str('GOOGLE_OAUTH2_CLIENT_SECRET', default='')

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
GOOGLE_GEMINI_API_KEY = env.str('GOOGLE_GEMINI_API_KEY', default='')
GEMINI_MODEL = env.str('GEMINI_MODEL', default='gemini-2.0-flash')
GEMINI_MAX_TOKENS = env.int('GEMINI_MAX_TOKENS', default=300)
GEMINI_TEMPERATURE = env.float('GEMINI_TEMPERATURE', default=0.7)

# Stripe Settings (never expose STRIPE_SECRET_KEY or STRIPE_WEBHOOK_SECRET to clients)
STRIPE_PUBLISHABLE_KEY = env.str('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = env.str('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = env.str('STRIPE_WEBHOOK_SECRET', default='')
STRIPE_PRICE_ID_PRO_MONTHLY = env.str('STRIPE_PRICE_ID_PRO_MONTHLY', default='')
STRIPE_PRICE_ID_PRO_YEARLY = env.str('STRIPE_PRICE_ID_PRO_YEARLY', default='')
STRIPE_PRICE_ID_ENTERPRISE = env.str('STRIPE_PRICE_ID_ENTERPRISE', default='')
STRIPE_PRICE_ID_AI_ADDON = env.str('STRIPE_PRICE_ID_AI_ADDON', default='')

# Donation link (Support page). Optional; set DONATION_URL in env to show the button.
DONATION_URL = env.str('DONATION_URL', default='').strip()

SOCIALACCOUNT_AUTO_SIGNUP = True
if DEBUG:
    SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
else:
    SOCIALACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# Email Configuration
# For local development, use console backend (emails printed to console)
# For production, configure SMTP settings in .env file
EMAIL_BACKEND = env.str('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env.str('EMAIL_HOST', default='localhost')
EMAIL_PORT = env.int('EMAIL_PORT', default=25)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=False)
EMAIL_USE_SSL = env.bool('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env.str('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env.str('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', default='webmaster@localhost')

# Baseline security headers (safe in development)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Production TLS / cookies / HSTS (Railway and other HTTPS proxies)
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True
    USE_X_FORWARDED_PORT = True

# Rate limiting (django-ratelimit); disabled automatically when RATELIMIT_ENABLE=False
RATELIMIT_ENABLE = env.bool('RATELIMIT_ENABLE', default=True)

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
SENTRY_DSN = env.str('SENTRY_DSN', default='')
SENTRY_ENVIRONMENT = env.str('SENTRY_ENVIRONMENT', default='development' if DEBUG else 'production')
SENTRY_TRACES_SAMPLE_RATE = env.float('SENTRY_TRACES_SAMPLE_RATE', default=0.1)

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