# Data migration: give all organizations full free features (admin_limit=10, ai_enabled=True)

from django.db import migrations


def unlock_organizations(apps, schema_editor):
    SchoolGroup = apps.get_model('schoolgroups', 'SchoolGroup')
    SchoolGroup.objects.all().update(admin_limit=10, ai_enabled=True)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('schoolgroups', '0005_schoolgroup_stripe_customer_id_and_more'),
    ]

    operations = [
        migrations.RunPython(unlock_organizations, noop_reverse),
    ]
