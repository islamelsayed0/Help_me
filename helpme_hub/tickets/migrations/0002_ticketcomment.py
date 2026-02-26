# Generated manually for TicketComment model (plan: Comments/updates)

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('body', models.TextField(help_text='Comment text')),
                ('is_internal', models.BooleanField(default=False, help_text='Internal note (visible only to admins)')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(help_text='User who wrote the comment', on_delete=django.db.models.deletion.CASCADE, related_name='ticket_comments', to=settings.AUTH_USER_MODEL)),
                ('ticket', models.ForeignKey(help_text='Ticket this comment belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='tickets.ticket')),
            ],
            options={
                'verbose_name': 'Ticket comment',
                'verbose_name_plural': 'Ticket comments',
                'ordering': ['created_at'],
            },
        ),
    ]
