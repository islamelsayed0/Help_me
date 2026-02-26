# Monitoring & Backup Guide

This guide covers error monitoring, performance monitoring, automated backups, and custom domain setup for HelpMe Hub.

## Table of Contents

1. [Error Monitoring with Sentry](#error-monitoring-with-sentry)
2. [Performance Monitoring](#performance-monitoring)
3. [Automated Database Backups](#automated-database-backups)
4. [Custom Domain Setup](#custom-domain-setup)
5. [Monitoring Dashboard](#monitoring-dashboard)

---

## Error Monitoring with Sentry

Sentry provides real-time error tracking and performance monitoring for your application.

### Setup Steps

1. **Create a Sentry Account**
   - Go to [https://sentry.io](https://sentry.io)
   - Sign up for a free account (free tier includes 5,000 events/month)
   - Create a new project and select "Django"

2. **Get Your DSN**
   - After creating the project, Sentry will show you a DSN (Data Source Name)
   - It looks like: `https://xxxxx@xxxxx.ingest.sentry.io/xxxxx`
   - Copy this DSN

3. **Configure Environment Variables**

   Add to your `.env` file (local) or Railway environment variables (production):

   ```env
   # Sentry Configuration
   SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
   SENTRY_ENVIRONMENT=production  # or 'development' for local
   SENTRY_TRACES_SAMPLE_RATE=0.1  # 10% of transactions (0.0 to 1.0)
   ```

4. **Verify Setup**

   - Sentry is automatically initialized when `SENTRY_DSN` is set and `DEBUG=False`
   - Test by triggering an error in your application
   - Check your Sentry dashboard for the error

### Sentry Features

- **Error Tracking**: Automatic capture of exceptions and errors
- **Performance Monitoring**: Track slow requests and database queries
- **Release Tracking**: Track which version of your app caused errors
- **User Context**: See which users encountered errors
- **Breadcrumbs**: See what happened before the error

### Configuration Options

- `SENTRY_DSN`: Your Sentry project DSN (required)
- `SENTRY_ENVIRONMENT`: Environment name (development, staging, production)
- `SENTRY_TRACES_SAMPLE_RATE`: Percentage of transactions to monitor (0.0 to 1.0)
  - Lower values = less performance overhead
  - Recommended: 0.1 (10%) for production

### Disabling Sentry

To disable Sentry, simply remove or leave `SENTRY_DSN` empty:

```env
SENTRY_DSN=
```

---

## Performance Monitoring

HelpMe Hub includes built-in performance monitoring middleware that tracks:

- Request duration
- Database query count
- Database query time
- Slow requests (>1 second)
- Slow database queries (>0.5 seconds)

### How It Works

The `PerformanceMonitoringMiddleware` automatically:

1. Tracks request start time
2. Counts database queries
3. Measures database query time
4. Logs warnings for slow requests/queries
5. Adds performance headers to responses

### Performance Headers

Every response includes these headers:

- `X-Request-Duration`: Request duration in seconds
- `X-DB-Query-Count`: Number of database queries
- `X-DB-Query-Time`: Total database query time in seconds

### Viewing Performance Metrics

**In Logs:**

Slow requests and database queries are logged with `WARNING` level:

```
WARNING: Slow request detected: GET /dashboard/
duration: 1.234, query_count: 15, query_time: 0.567
```

**In Sentry:**

If Sentry is configured, performance data is automatically sent to Sentry for visualization.

**In Railway:**

Railway logs show performance warnings. You can also use Railway's built-in metrics dashboard.

### Customizing Thresholds

Edit `helpme_hub/middleware.py` to adjust thresholds:

```python
class PerformanceMonitoringMiddleware(MiddlewareMixin):
    SLOW_REQUEST_THRESHOLD = 1.0  # seconds
    SLOW_DB_THRESHOLD = 0.5  # seconds
```

---

## Automated Database Backups

Automated database backups ensure you can recover from data loss or corruption.

### Manual Backup

Run the backup command manually:

```bash
python manage.py backup_database
```

This creates a backup in `backups/db_backup_YYYYMMDD_HHMMSS.sql`

### Backup Options

**Compress backup:**

```bash
python manage.py backup_database --compress
```

**Custom output location:**

```bash
python manage.py backup_database --output /path/to/backup.sql
```

**Keep only recent backups:**

```bash
python manage.py backup_database --keep 10  # Keep only 10 most recent backups
```

### Automated Backups on Railway

#### Option 1: Railway Cron Jobs (Recommended)

1. **Create a backup script:**

   Create `scripts/backup.sh`:

   ```bash
   #!/bin/bash
   cd /app
   source venv/bin/activate
   python manage.py backup_database --compress --keep 30
   ```

2. **Set up Railway Cron:**

   - In Railway dashboard, go to your project
   - Add a new service → Cron Job
   - Schedule: `0 2 * * *` (daily at 2 AM UTC)
   - Command: `bash scripts/backup.sh`

3. **Store backups:**

   - Option A: Use Railway volumes to store backups
   - Option B: Upload to S3/Cloud Storage (see Option 2)

#### Option 2: External Backup Service

Use a service like:
- **Backupify**: Automated PostgreSQL backups
- **pgBackRest**: Advanced PostgreSQL backup tool
- **AWS S3**: Store backups in S3 bucket

**Example: Upload to S3**

Modify the backup command to upload after backup:

```python
# In backup_database.py, add S3 upload after backup completes
import boto3

s3_client = boto3.client('s3')
s3_client.upload_file(str(output_path), 'your-bucket', f'backups/{output_path.name}')
```

#### Option 3: Railway PostgreSQL Backups

Railway provides automatic PostgreSQL backups:

- Go to your PostgreSQL service in Railway
- Check "Backups" section
- Railway automatically backs up daily
- Restore from Railway dashboard if needed

### Backup Restoration

**PostgreSQL:**

```bash
# Restore from backup file
psql -h localhost -U username -d database_name < backup.sql

# Or using Railway CLI
railway run psql < backup.sql
```

**SQLite:**

```bash
# Simply copy the backup file back
cp backup.sql db.sqlite3
```

### Backup Best Practices

1. **Frequency**: Daily backups for production, weekly for development
2. **Retention**: Keep 30 days of backups (configurable)
3. **Testing**: Test restore procedures monthly
4. **Off-site**: Store backups in a different location/service
5. **Encryption**: Encrypt sensitive backups
6. **Monitoring**: Alert if backups fail

---

## Custom Domain Setup

Set up a custom domain for your HelpMe Hub deployment on Railway.

### Step 1: Add Domain in Railway

1. Go to your Railway project dashboard
2. Click on your web service
3. Go to **Settings** → **Networking**
4. Click **Add Domain**
5. Enter your domain (e.g., `helpmehub.com` or `www.helpmehub.com`)

### Step 2: Configure DNS

Railway will provide DNS records to add. Typically:

**For root domain (helpmehub.com):**

```
Type: CNAME
Name: @
Value: your-app.railway.app
```

**For www subdomain (www.helpmehub.com):**

```
Type: CNAME
Name: www
Value: your-app.railway.app
```

**Or use A record (if CNAME not supported for root):**

```
Type: A
Name: @
Value: [Railway IP address]
```

### Step 3: Update Django Settings

Update `ALLOWED_HOSTS` in Railway environment variables:

```env
ALLOWED_HOSTS=helpmehub.com,www.helpmehub.com,your-app.railway.app
```

### Step 4: Update Site Domain

After deployment, update Django's Site model:

```bash
railway run python manage.py shell
```

```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'helpmehub.com'
site.name = 'HelpMe Hub'
site.save()
```

### Step 5: SSL Certificate

Railway automatically provisions SSL certificates via Let's Encrypt. Wait 5-10 minutes after DNS propagation for SSL to activate.

### Step 6: Verify

1. Visit your custom domain
2. Check that SSL is active (padlock icon)
3. Test all functionality
4. Verify emails use the custom domain

### Troubleshooting

**Domain not resolving:**
- Wait 24-48 hours for DNS propagation
- Verify DNS records are correct
- Check DNS with `dig` or `nslookup`

**SSL not working:**
- Ensure DNS is fully propagated
- Wait 10-15 minutes after DNS setup
- Check Railway logs for SSL errors

**Redirect loops:**
- Verify `SECURE_SSL_REDIRECT` is set correctly
- Check `ALLOWED_HOSTS` includes your domain

---

## Monitoring Dashboard

### Railway Built-in Metrics

Railway provides:
- Request metrics (requests/second, response times)
- Error rates
- Resource usage (CPU, memory)
- Logs viewer

Access via Railway dashboard → Your service → Metrics

### Sentry Dashboard

If Sentry is configured:
- Error trends
- Performance metrics
- User impact
- Release tracking

Access via [https://sentry.io](https://sentry.io)

### Custom Monitoring (Optional)

Consider adding:
- **UptimeRobot**: Monitor uptime and alert on downtime
- **New Relic**: Advanced application performance monitoring
- **Datadog**: Infrastructure and application monitoring
- **Grafana**: Custom dashboards and metrics

---

## Summary Checklist

- [ ] Sentry account created and DSN configured
- [ ] Performance monitoring middleware active
- [ ] Automated backups scheduled
- [ ] Custom domain configured (if applicable)
- [ ] SSL certificate active
- [ ] Monitoring dashboards set up
- [ ] Backup restoration tested
- [ ] Alerts configured for critical issues

---

**Need Help?**

- Sentry Docs: [https://docs.sentry.io/platforms/python/guides/django/](https://docs.sentry.io/platforms/python/guides/django/)
- Railway Docs: [https://docs.railway.app/](https://docs.railway.app/)
- Django Deployment: [https://docs.djangoproject.com/en/4.2/howto/deployment/](https://docs.djangoproject.com/en/4.2/howto/deployment/)
