"""
Django settings for helpme_hub project.

Generated for Phase 1: Foundation
"""

from pathlib import Path
import os
import re
import sys
from urllib.parse import quote_plus

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


def _sanitize_connection_string(value):
    """Strip BOM / wrapping quotes so pasted Railway URLs parse correctly."""
    if not value:
        return ''
    s = value.strip().lstrip('\ufeff')
    while len(s) >= 2 and s[0] == s[-1] and s[0] in ('"', "'"):
        s = s[1:-1].strip()
    return s


def _env_first_nonempty(*keys):
    """First non-empty env value among keys (Railway uses PG* and POSTGRES_* names)."""
    for key in keys:
        raw = os.environ.get(key)
        if raw is None:
            continue
        s = _sanitize_connection_string(str(raw))
        if s:
            return s
    return ''


def _database_url_from_pg_env():
    """Build postgres URL from PG* or POSTGRES_* split vars (Railway references)."""
    host = _env_first_nonempty('PGHOST', 'POSTGRES_HOST')
    port = _env_first_nonempty('PGPORT', 'POSTGRES_PORT') or '5432'
    user = _env_first_nonempty('PGUSER', 'POSTGRES_USER')
    password = (
        os.environ.get('PGPASSWORD')
        if os.environ.get('PGPASSWORD') is not None
        else os.environ.get('POSTGRES_PASSWORD')
    )
    if password is None:
        password = ''
    password = str(password)
    name = _env_first_nonempty('PGDATABASE', 'POSTGRES_DB', 'POSTGRES_DATABASE')
    if not (host and user and name):
        return ''
    return (
        f'postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{name}'
    )


def _database_url_has_hostname(url):
    """True when parsed config has HOST (avoids socket-only postgresql:///db)."""
    if not url:
        return False
    try:
        cfg = dj_database_url.parse(url)
    except (ValueError, TypeError):
        return False
    host = (cfg.get('HOST') or '').strip()
    return bool(host)


def _repair_postgres_url_missing_host(url):
    """
    postgresql://user:pass@/dbname (no host) → insert PGHOST:PORT from env.
    Railway sometimes supplies this shape; PGHOST may be referenced separately.
    """
    if not url or _database_url_has_hostname(url):
        return url
    host = _env_first_nonempty('PGHOST', 'POSTGRES_HOST')
    if not host:
        return url
    port = _env_first_nonempty('PGPORT', 'POSTGRES_PORT') or '5432'
    m = re.match(
        r'^(postgres(?:ql)?://[^@]+)@/([^?#]*)(.*)$',
        url.strip(),
        re.IGNORECASE,
    )
    if not m:
        return url
    prefix, dbpath, rest = m.group(1), m.group(2), m.group(3)
    dbname = dbpath.lstrip('/')
    if not dbname:
        return url
    return f'{prefix}@{host}:{port}/{dbname}{rest}'


def _railway_database_url_candidates():
    """
    URL-shaped vars as injected by the host (Railway).
    Read os.environ directly so values match the platform (django-environ is not involved).
    """
    keys = ('DATABASE_URL', 'DATABASE_PRIVATE_URL', 'DATABASE_PUBLIC_URL')
    return [(k, _sanitize_connection_string(os.environ.get(k, ''))) for k in keys]


def _resolve_database_url():
    """Use first URL var that includes a host; else PG* composite (Railway references)."""
    candidates = _railway_database_url_candidates()
    for _key, url in candidates:
        if url and _database_url_has_hostname(url):
            return url, 'env_url'

    for _key, url in candidates:
        if url:
            repaired = _repair_postgres_url_missing_host(url)
            if repaired != url and _database_url_has_hostname(repaired):
                return repaired, 'env_url_repaired'

    built = _database_url_from_pg_env()
    bad_direct = any(u for _k, u in candidates if u and not _database_url_has_hostname(u))
    if built:
        return built, 'pg_env_fallback' if bad_direct else 'pg_env'

    # Do not return host-less URLs: they make psycopg2 use /var/run/postgresql sockets.
    return '', 'none'


_db_url, _ = _resolve_database_url()
USE_SQLITE = env.bool('USE_SQLITE', default=False)

if IS_PRODUCTION:
    if USE_SQLITE:
        raise ImproperlyConfigured('USE_SQLITE must not be enabled in production.')
    if not _db_url:
        hostless = [
            k
            for k, u in _railway_database_url_candidates()
            if u and not _database_url_has_hostname(u)
        ]
        if hostless:
            raw_db = os.environ.get('DATABASE_URL') or ''
            hint = ''
            if '${' in raw_db or '{{' in raw_db:
                hint = (
                    ' DATABASE_URL looks like an unresolved template (${{…}}): in Railway use '
                    '"Variable Reference" from the Postgres service, not a literal placeholder string.'
                )
            raise ImproperlyConfigured(
                'Database URL variable(s) are set but have no hostname: %(vars)s.%(template)s '
                'Fix: Help_me → Variables → set DATABASE_URL using Railway “Reference” to Postgres '
                'DATABASE_URL or DATABASE_PUBLIC_URL (must look like postgresql://user:pass@host:port/db). '
                'Or add references from Postgres for POSTGRES_HOST, POSTGRES_USER, '
                'POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT (or PG* equivalents).'
                % {'vars': ', '.join(hostless), 'template': hint}
            )
        raise ImproperlyConfigured(
            'A database connection is required in production. '
            'On Railway: reference Postgres DATABASE_* URL or PG*/POSTGRES_* host variables '
            'onto this web service.'
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