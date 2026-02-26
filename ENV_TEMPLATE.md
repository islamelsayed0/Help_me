# Environment Variables Template

This file shows what environment variables are needed. Copy this to `.env` file for local development.

**Important:** The actual `.env` file is in `.gitignore` and should never be committed to Git.

## Create .env File

```bash
cp .env.example .env
# Then edit .env with your actual values
```

## Required Environment Variables

### Django Settings

```env
# Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=your-secret-key-here

# Set to False in production
DEBUG=True

# Comma separated list of allowed hostnames
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Database

```env
# For local development with PostgreSQL:
DATABASE_URL=postgresql://user:password@localhost:5432/helpmehub

# For local development with SQLite (leave empty or don't set):
# DATABASE_URL=

# For Railway production (automatically set by Railway):
# DATABASE_URL is provided automatically
```

### Google OAuth (Optional)

```env
# Get from Google Cloud Console: https://console.cloud.google.com/
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id-here
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret-here
```

### Email Settings (Optional)

```env
# For development, use console backend:
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# For production:
# EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
# EMAIL_HOST=smtp.gmail.com
# EMAIL_PORT=587
# EMAIL_USE_TLS=True
# EMAIL_HOST_USER=your-email@gmail.com
# EMAIL_HOST_PASSWORD=your-email-password
```

### Donation Link (Support page)

HelpMe Hub is free. The **Support** page can show a Donate button that links to your donation URL (e.g. Stripe Payment Link, Ko-fi, Buy Me a Coffee). Optional; leave empty to hide the button.

```env
# Your donation page URL (opens in new tab when user clicks Donate)
DONATION_URL=https://buy.stripe.com/your-payment-link-id
```

### Static Files

```env
STATIC_URL=/static/
MEDIA_URL=/media/
```

### Railway (Production Only)

```env
# Automatically set by Railway
RAILWAY_ENVIRONMENT=production
```

### Sentry Error Monitoring (Optional)

```env
# Get your DSN from https://sentry.io/settings/projects/
# Sentry is only enabled when SENTRY_DSN is set and DEBUG=False
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
SENTRY_ENVIRONMENT=production  # or 'development' for local
SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions (0.0 to 1.0)
```

## How to Get Values

### SECRET_KEY
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Google OAuth Credentials
1. Go to https://console.cloud.google.com/
2. Create a new project (or select existing)
3. Enable Google+ API (or Google Identity API)
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/accounts/google/login/callback/`
   **Important:** The callback URL must be exactly `/accounts/google/login/callback/` (not `/accounts/google/callback/`)
6. Copy Client ID and Client Secret

### Stripe Configuration

### DATABASE_URL Format
```
postgresql://username:password@host:port/database_name
```

Example:
```
postgresql://myuser:mypassword@localhost:5432/helpmehub
```

## Production (Railway)

On Railway, set these in the web service environment variables:
- `SECRET_KEY` - Generate a new one for production
- `DEBUG=False`
- `ALLOWED_HOSTS=your-app-name.up.railway.app,*.railway.app`
- `DATABASE_URL` - Automatically provided by Railway PostgreSQL
- `GOOGLE_OAUTH2_CLIENT_ID` - Your Google OAuth client ID
- `GOOGLE_OAUTH2_CLIENT_SECRET` - Your Google OAuth client secret
- `DONATION_URL` - Optional; your donation page URL (e.g. Stripe Payment Link) for the Support page
- `STATIC_URL=/static/`
- `MEDIA_URL=/media/`
- `RAILWAY_ENVIRONMENT=production`
- `SENTRY_DSN` - Your Sentry DSN (optional, for error monitoring)
- `SENTRY_ENVIRONMENT=production` - Environment name for Sentry
- `SENTRY_TRACES_SAMPLE_RATE=0.1` - Performance monitoring sample rate

## Security Reminders

- ✅ Never commit `.env` file to Git
- ✅ Use different secrets for development and production
- ✅ Rotate secrets regularly
- ✅ Don't share `.env` files
- ✅ Use `.env.example` as a template (with placeholder values)

