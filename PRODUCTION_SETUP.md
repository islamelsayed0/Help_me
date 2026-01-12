# Production Setup Guide

This guide will help you configure HelpMe Hub for production deployment on Railway.

## Prerequisites

- ✅ Railway account created
- ✅ PostgreSQL database created on Railway
- ✅ Stripe account created (for payment processing)
- ✅ Domain name (optional, Railway provides default domain)

## Step 1: Railway Environment Variables

Set these environment variables in your Railway project dashboard:

### Required Settings

```env
# Django Settings
SECRET_KEY=your-super-secret-production-key-here
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app,yourdomain.com

# Database (Railway automatically provides this)
DATABASE_URL=postgresql://postgres:password@host:port/railway
```

### Email Configuration (Required for Production)

```env
# Email Backend - Use SMTP for production
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Alternative: Use SendGrid, Mailgun, etc.
# EMAIL_HOST=smtp.sendgrid.net
# EMAIL_PORT=587
# EMAIL_HOST_USER=apikey
# EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

### Stripe Configuration

```env
# Stripe Settings (from your Stripe dashboard)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Price IDs (create products/prices in Stripe dashboard)
STRIPE_PRICE_ID_PRO_MONTHLY=price_...
STRIPE_PRICE_ID_PRO_YEARLY=price_...
STRIPE_PRICE_ID_ENTERPRISE=price_...
STRIPE_PRICE_ID_AI_ADDON=price_...
```

### Google OAuth (Optional)

```env
GOOGLE_OAUTH2_CLIENT_ID=your-google-client-id
GOOGLE_OAUTH2_CLIENT_SECRET=your-google-client-secret
```

### Google Gemini AI (Optional)

```env
GOOGLE_GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-2.0-flash
GEMINI_MAX_TOKENS=1000
GEMINI_TEMPERATURE=0.7
```

### Static Files

```env
STATIC_URL=/static/
MEDIA_URL=/media/
```

## Step 2: Railway Deployment

1. **Connect your GitHub repository** to Railway
2. **Create a PostgreSQL service** in Railway
3. **Create a Web Service** and link it to your database
4. **Set all environment variables** in Railway dashboard
5. **Configure build settings:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn helpme_hub.wsgi:application --bind 0.0.0.0:$PORT`
6. **Deploy!** Railway will automatically deploy on git push

## Step 3: Post-Deployment Setup

### Run Migrations

After first deployment, run migrations:

```bash
# Via Railway CLI
railway run python manage.py migrate

# Or via Railway dashboard -> Deployments -> Run Command
python manage.py migrate
```

### Create Superuser

```bash
railway run python manage.py createsuperuser
```

### Collect Static Files

```bash
railway run python manage.py collectstatic --noinput
```

### Update Site Domain

Update Django Site domain to match your Railway domain:

```bash
railway run python manage.py shell
```

Then in Python shell:

```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'your-app.railway.app'  # Or your custom domain
site.name = 'HelpMe Hub'
site.save()
```

## Step 4: Stripe Webhook Setup

1. **Create a webhook endpoint** in Stripe Dashboard
   - URL: `https://your-app.railway.app/accounts/stripe/webhook/`
   - Events to listen for:
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`

2. **Copy the webhook secret** and add it to Railway environment variables as `STRIPE_WEBHOOK_SECRET`

3. **Test the webhook** using Stripe CLI:

```bash
stripe listen --forward-to https://your-app.railway.app/accounts/stripe/webhook/
```

## Step 5: Email Service Setup

### Option 1: Gmail SMTP

1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use your Gmail address and app password in `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`

### Option 2: SendGrid (Recommended)

1. Create a SendGrid account
2. Create an API key with Mail Send permissions
3. Verify your sender email/domain
4. Configure:
   ```env
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_PORT=587
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=your-sendgrid-api-key
   ```

### Option 3: Mailgun

1. Create a Mailgun account
2. Verify your domain
3. Use your Mailgun SMTP credentials

## Step 6: Custom Domain (Optional)

1. **Add custom domain** in Railway dashboard
2. **Update ALLOWED_HOSTS** to include your domain
3. **Update Site domain** in Django admin
4. **Configure DNS** records as instructed by Railway

## Step 7: Monitoring & Logs

Railway automatically provides:
- **Application logs** in Railway dashboard
- **Build logs** for deployment issues

For production monitoring, consider:
- **Sentry** for error tracking
- **Railway Metrics** for performance monitoring
- **Uptime monitoring** (UptimeRobot, etc.)

## Step 8: Backup Strategy

### Database Backups

Railway provides automatic PostgreSQL backups, but consider:
- Daily database dumps
- Off-site backup storage
- Test restore procedures

### Static Files

- If using S3/CloudFront, configure backups
- If using WhiteNoise (default), files are served from app

## Production Checklist

Before going live:

- [ ] All environment variables set in Railway
- [ ] DEBUG=False in production
- [ ] SECRET_KEY is strong and unique
- [ ] ALLOWED_HOSTS includes your domain
- [ ] Database migrations run
- [ ] Superuser created
- [ ] Static files collected
- [ ] Site domain updated
- [ ] Email service configured and tested
- [ ] Stripe webhook configured and tested
- [ ] SSL certificate active (automatic on Railway)
- [ ] Error monitoring set up
- [ ] Backup strategy in place
- [ ] Performance testing completed

## Testing in Production

1. **Test user registration** - verify welcome email sent
2. **Test organization join** - verify approval email sent
3. **Test ticket creation** - verify assignment email sent
4. **Test Stripe checkout** - use test mode first
5. **Test webhook** - verify subscription updates work
6. **Test email delivery** - check spam folder

## Security Notes

- ✅ Never commit `.env` files
- ✅ Use strong, unique SECRET_KEY
- ✅ Keep dependencies updated
- ✅ Enable 2FA on Railway account
- ✅ Use app-specific passwords for email
- ✅ Rotate API keys regularly
- ✅ Monitor logs for suspicious activity

## Troubleshooting

### Emails not sending
- Check EMAIL_BACKEND is set to SMTP
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- Check spam folder
- Test with console backend first

### Static files not loading
- Run `collectstatic` command
- Check STATIC_ROOT setting
- Verify WhiteNoise middleware is enabled

### Database connection issues
- Verify DATABASE_URL is set correctly
- Check Railway database is running
- Verify network connectivity

### Stripe webhook not working
- Verify webhook URL is correct
- Check STRIPE_WEBHOOK_SECRET matches
- Test with Stripe CLI first
- Check Railway logs for errors

## Support

For Railway-specific issues, see [Railway Documentation](https://docs.railway.app/).

For Django deployment issues, see [Django Deployment Checklist](https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/).

---

**Ready for production!** 🚀
