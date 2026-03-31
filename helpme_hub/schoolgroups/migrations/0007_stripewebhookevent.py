# Generated manually for Stripe webhook idempotency

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schoolgroups', '0006_unlock_free_organizations'),
    ]

    operations = [
        migrations.CreateModel(
            name='StripeWebhookEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_event_id', models.CharField(db_index=True, max_length=255, unique=True)),
                ('event_type', models.CharField(blank=True, max_length=255)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Stripe webhook event',
                'verbose_name_plural': 'Stripe webhook events',
                'ordering': ['-created_at'],
            },
        ),
    ]
