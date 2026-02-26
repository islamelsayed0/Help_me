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

#### Step 1: Get Your Stripe API Keys

1. Go to [Stripe Dashboard](https://dashboard.stripe.com/)
2. Navigate to **Developers** → **API keys**
3. You'll see two keys:
   - **Publishable key** (starts with `pk_live_...` or `pk_test_...`)
   - **Secret key** (starts with `sk_live_...` or `sk_test_...`)
4. **Important:** 
   - Use **test keys** (`pk_test_...` and `sk_test_...`) for development/testing
   - Use **live keys** (`pk_live_...` and `sk_live_...`) for production
   - Toggle between test and live mode using the toggle switch in Stripe Dashboard

#### Step 2: Create Products and Prices

You need to create 4 products in Stripe Dashboard:

1. **Go to Products** → **Add product**

2. **Create Pro Plan - Monthly:**
   - Name: `Pro Plan - Monthly`
   - Description: `Monthly subscription to Pro Plan`
   - Pricing model: `Standard pricing`
   - Price: Set your monthly price (e.g., `$29.00`)
   - Billing period: `Monthly`
   - Click **Save product**
   - **Copy the Price ID** (starts with `price_...`) - this is your `STRIPE_PRICE_ID_PRO_MONTHLY`

3. **Create Pro Plan - Yearly:**
   - Name: `Pro Plan - Yearly`
   - Description: `Yearly subscription to Pro Plan`
   - Pricing model: `Standard pricing`
   - Price: Set your yearly price (e.g., `$290.00`)
   - Billing period: `Yearly`
   - Click **Save product**
   - **Copy the Price ID** - this is your `STRIPE_PRICE_ID_PRO_YEARLY`

4. **Create Enterprise Plan:**
   - Name: `Enterprise Plan`
   - Description: `Enterprise subscription plan`
   - Pricing model: `Standard pricing`
   - Price: Set your enterprise price (e.g., `$99.00`)
   - Billing period: `Monthly` or `Yearly` (choose based on your pricing model)
   - Click **Save product**
   - **Copy the Price ID** - this is your `STRIPE_PRICE_ID_ENTERPRISE`

5. **Create AI Add-On:**
   - Name: `AI Add-On`
   - Description: `AI chat add-on subscription`
   - Pricing model: `Standard pricing`
   - Price: `$7.00`
   - Billing period: `Monthly`
   - Click **Save product**
   - **Copy the Price ID** - this is your `STRIPE_PRICE_ID_AI_ADDON`

**Note:** To find Price IDs after creation, go to **Products** → click on a product → scroll to **Pricing** section → click on the price → the Price ID is shown at the top.

#### Step 3: Set Up Webhook Endpoint

1. **Go to Developers** → **Webhooks** → **Add endpoint**

2. **Set the endpoint URL:**
   - For production: `https://your-app.railway.app/accounts/stripe/webhook/`
   - Replace `your-app.railway.app` with your actual Railway domain
   - For local testing, use [Stripe CLI](https://stripe.com/docs/stripe-cli) to forward webhooks

3. **Select events to listen for:**
   - `checkout.session.completed` - When a customer completes checkout
   - `customer.subscription.updated` - When subscription is updated
   - `customer.subscription.deleted` - When subscription is cancelled
   - `invoice.payment_succeeded` - When payment succeeds
   - `invoice.payment_failed` - When payment fails

4. **Click Add endpoint**

5. **Copy the Signing secret:**
   - After creating the endpoint, click on it
   - In the **Signing secret** section, click **Reveal** or **Click to reveal**
   - Copy the secret (starts with `whsec_...`)
   - This is your `STRIPE_WEBHOOK_SECRET`

**Important:** The webhook secret is only shown once when you first create the endpoint. If you lose it, you'll need to create a new endpoint or regenerate the secret.

#### Step 4: Add to Environment Variables

Add these to your Railway environment variables:

```env
# Stripe API Keys (from Step 1)
STRIPE_PUBLISHABLE_KEY=pk_live_51SoUhZACGLosuIt5yA13DAr9gvSMSAPrLtJdXJ6ofuXyPHCAx6MyaMXcKGli9L2pBTIsOp8iX25rbmqUEgHSM8Ye00QE0l0PBN
STRIPE_SECRET_KEY=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

# Stripe Webhook Secret (from Step 3)
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe Price IDs (from Step 2)
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

## Step 4: Stripe Webhook Testing

After setting up your webhook endpoint (see Step 1, Section 3 above), test it:

### Local Testing with Stripe CLI

1. **Install Stripe CLI:**
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe
   
   # Or download from: https://stripe.com/docs/stripe-cli
   ```

2. **Login to Stripe:**
   ```bash
   stripe login
   ```

3. **Forward webhooks to local server:**
   ```bash
   stripe listen --forward-to http://localhost:8000/accounts/stripe/webhook/
   ```

4. **Test webhook events:**
   ```bash
   stripe trigger checkout.session.completed
   ```

### Production Testing

1. **Use Stripe Dashboard** → **Webhooks** → Click on your endpoint
2. **Send test webhook** from the dashboard
3. **Check Railway logs** to verify webhook is received and processed
4. **Verify subscription updates** in your application

### Troubleshooting Webhooks

- **Webhook not received:** Check Railway logs, verify webhook URL is correct
- **Signature verification failed:** Ensure `STRIPE_WEBHOOK_SECRET` matches the signing secret
- **Events not processing:** Check application logs for errors in webhook handler

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
- **Sentry** for error tracking (see [MONITORING_AND_BACKUPS.md](MONITORING_AND_BACKUPS.md))
- **Railway Metrics** for performance monitoring
- **Uptime monitoring** (UptimeRobot, etc.)

### Setting Up Sentry (Recommended)

1. Create account at [https://sentry.io](https://sentry.io)
2. Create a Django project and copy your DSN
3. Add to Railway environment variables:
   ```env
   SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
   SENTRY_ENVIRONMENT=production
   SENTRY_TRACES_SAMPLE_RATE=0.1
   ```

See [MONITORING_AND_BACKUPS.md](MONITORING_AND_BACKUPS.md) for detailed setup instructions.

## Step 8: Backup Strategy

### Database Backups

Railway provides automatic PostgreSQL backups, but consider:
- Daily database dumps using `python manage.py backup_database`
- Automated backups via Railway Cron (see [MONITORING_AND_BACKUPS.md](MONITORING_AND_BACKUPS.md))
- Off-site backup storage
- Test restore procedures

### Static Files

- If using S3/CloudFront, configure backups
- If using WhiteNoise (default), files are served from app

See [MONITORING_AND_BACKUPS.md](MONITORING_AND_BACKUPS.md) for detailed backup setup instructions.

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
