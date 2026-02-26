"""
Management command to seed demo data for local testing and demos.

Usage:
    python manage.py seed_demo_data

Creates:
- One demo school organization and one demo business organization
- Superadmin, org admins, and staff users
- Sample chats, tickets, knowledge articles, and inventory items
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from schoolgroups.models import SchoolGroup, SchoolGroupMembership
from chats.models import Chat
from tickets.models import Ticket
from knowledge.models import Article
from inventory.models import InventoryItem


User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data (organizations, users, chats, tickets, articles, inventory)."

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # Superadmin
        superadmin, _ = User.objects.get_or_create(
            email="superadmin@demo.local",
            defaults={
                "username": "superadmin_demo",
                "role": "superadmin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if not superadmin.has_usable_password():
            superadmin.set_password("DemoPass123!")
            superadmin.save()

        # Demo organizations
        school_org, _ = SchoolGroup.objects.get_or_create(
            name="Demo School",
            defaults={
                "description": "Demo school organization for testing HelpMe Hub.",
                "created_by": superadmin,
                "plan": "free",
                "admin_limit": 10,
                "ai_enabled": True,
            },
        )

        business_org, _ = SchoolGroup.objects.get_or_create(
            name="Demo Business",
            defaults={
                "description": "Demo business organization for testing HelpMe Hub.",
                "created_by": superadmin,
                "plan": "free",
                "admin_limit": 10,
                "ai_enabled": True,
            },
        )

        # Admins and staff
        school_admin, _ = User.objects.get_or_create(
            email="schooladmin@demo.local",
            defaults={
                "username": "school_admin_demo",
                "role": "admin",
            },
        )
        if not school_admin.has_usable_password():
            school_admin.set_password("DemoPass123!")
            school_admin.save()

        school_staff, _ = User.objects.get_or_create(
            email="teacher@demo.local",
            defaults={
                "username": "teacher_demo",
                "role": "user",
            },
        )
        if not school_staff.has_usable_password():
            school_staff.set_password("DemoPass123!")
            school_staff.save()

        business_admin, _ = User.objects.get_or_create(
            email="bizadmin@demo.local",
            defaults={
                "username": "business_admin_demo",
                "role": "admin",
            },
        )
        if not business_admin.has_usable_password():
            business_admin.set_password("DemoPass123!")
            business_admin.save()

        business_staff, _ = User.objects.get_or_create(
            email="staff@demo.local",
            defaults={
                "username": "staff_demo",
                "role": "user",
            },
        )
        if not business_staff.has_usable_password():
            business_staff.set_password("DemoPass123!")
            business_staff.save()

        # Memberships
        for org, admin, staff in [
            (school_org, school_admin, school_staff),
            (business_org, business_admin, business_staff),
        ]:
            SchoolGroupMembership.objects.get_or_create(
                user=admin,
                school_group=org,
                defaults={"status": "accepted"},
            )
            SchoolGroupMembership.objects.get_or_create(
                user=staff,
                school_group=org,
                defaults={"status": "accepted"},
            )

        # Sample chats and tickets for school_org
        chat1, _ = Chat.objects.get_or_create(
            user=school_staff,
            school_group=school_org,
            defaults={"assigned_to": school_admin},
        )
        Ticket.objects.get_or_create(
            user=school_staff,
            school_group=school_org,
            chat=chat1,
            title="Projector not working in Room 101",
            defaults={
                "description": "The projector in Room 101 won't turn on. Tried unplugging and plugging back in.",
                "status": "open",
                "priority": "high",
            },
        )

        # Sample chats and tickets for business_org
        chat2, _ = Chat.objects.get_or_create(
            user=business_staff,
            school_group=business_org,
            defaults={"assigned_to": business_admin},
        )
        Ticket.objects.get_or_create(
            user=business_staff,
            school_group=business_org,
            chat=chat2,
            title="VPN connection issues",
            defaults={
                "description": "Cannot connect to VPN from home network.",
                "status": "in_progress",
                "priority": "medium",
            },
        )

        # Knowledge base articles (global + org-specific)
        Article.objects.get_or_create(
            title="Getting started with HelpMe Hub",
            defaults={
                "author": superadmin,
                "content": "This article explains how to use HelpMe Hub for your school or business.",
                "category": "general",
                "status": "published",
                "published_at": timezone.now(),
            },
        )
        Article.objects.get_or_create(
            title="Classroom Wi-Fi troubleshooting",
            school_group=school_org,
            defaults={
                "author": school_admin,
                "content": "Step-by-step guide for fixing common classroom Wi-Fi issues.",
                "category": "technical",
                "status": "published",
                "published_at": timezone.now(),
            },
        )
        Article.objects.get_or_create(
            title="Office printer setup",
            school_group=business_org,
            defaults={
                "author": business_admin,
                "content": "How to install and configure the main office printer.",
                "category": "technical",
                "status": "published",
                "published_at": timezone.now(),
            },
        )

        # Inventory items
        InventoryItem.objects.get_or_create(
            school_group=school_org,
            name="Teacher Laptop",
            item_number="SCH-LAP-001",
            defaults={
                "location": "IT Closet",
                "serial_number": "ABC123SCHOOL",
                "buy_link": "",
                "quantity": 5,
                "min_stock": 2,
                "notes": "Reserved for new teachers.",
            },
        )
        InventoryItem.objects.get_or_create(
            school_group=business_org,
            name="Office Monitor",
            item_number="BUS-MON-001",
            defaults={
                "location": "Storage Room",
                "serial_number": "",
                "buy_link": "",
                "quantity": 8,
                "min_stock": 3,
                "notes": "24-inch monitors for staff.",
            },
        )

        self.stdout.write(self.style.SUCCESS("✓ Demo data seeded successfully."))

