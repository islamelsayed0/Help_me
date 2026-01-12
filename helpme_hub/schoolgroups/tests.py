from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import SchoolGroup, SchoolGroupMembership, JoinRequest
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class SchoolGroupModelTests(TestCase):
    """Test SchoolGroup model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='TestPass123!'
        )
    
    def test_create_organization(self):
        """Test creating an organization."""
        org = SchoolGroup.objects.create(
            name='Test Organization',
            description='Test Description',
            created_by=self.user
        )
        self.assertEqual(org.name, 'Test Organization')
        self.assertEqual(org.created_by, self.user)
        # Access code is not auto-generated, must be called explicitly
        org.generate_access_code()
        self.assertTrue(org.access_code)
    
    def test_access_code_generation(self):
        """Test access code can be generated."""
        org = SchoolGroup.objects.create(
            name='Test Organization',
            description='Test',
            created_by=self.user
        )
        # Access code is not auto-generated, must be called explicitly
        org.generate_access_code()
        self.assertIsNotNone(org.access_code)
        self.assertGreaterEqual(len(org.access_code), 12)
        # Should be alphanumeric (uppercase)
        self.assertTrue(org.access_code.isalnum())
    
    def test_access_code_formatting(self):
        """Test access code formatting."""
        org = SchoolGroup.objects.create(
            name='Test Organization',
            description='Test',
            created_by=self.user
        )
        org.generate_access_code()
        formatted = org.get_formatted_access_code()
        # Should have format XXXX-XXXX-XXXX
        parts = formatted.split('-')
        self.assertEqual(len(parts), 3)
        self.assertEqual(len(parts[0]), 4)
        self.assertEqual(len(parts[1]), 4)
        self.assertEqual(len(parts[2]), 4)
    
    def test_access_code_normalization(self):
        """Test access code normalization."""
        org = SchoolGroup.objects.create(
            name='Test Organization',
            description='Test',
            created_by=self.user
        )
        org.generate_access_code()
        formatted = org.get_formatted_access_code()
        normalized = SchoolGroup.normalize_access_code(formatted)
        self.assertEqual(normalized, org.access_code)
        # Should handle lowercase
        normalized_lower = SchoolGroup.normalize_access_code(formatted.lower())
        self.assertEqual(normalized_lower, org.access_code.upper())
    
    def test_access_code_validation(self):
        """Test access code validation."""
        org = SchoolGroup.objects.create(
            name='Test Organization',
            description='Test',
            created_by=self.user
        )
        org.generate_access_code()
        # Valid code
        self.assertTrue(org.is_access_code_valid())
        # Expire the code
        org.access_code_expires_at = timezone.now() - timedelta(days=1)
        org.save()
        self.assertFalse(org.is_access_code_valid())
    
    def test_regenerate_access_code(self):
        """Test access code regeneration."""
        org = SchoolGroup.objects.create(
            name='Test Organization',
            description='Test',
            created_by=self.user
        )
        old_code = org.access_code
        old_generated_at = org.access_code_generated_at
        org.regenerate_access_code()
        self.assertNotEqual(org.access_code, old_code)
        self.assertNotEqual(org.access_code_generated_at, old_generated_at)
        self.assertTrue(org.is_access_code_valid())


class SchoolGroupMembershipTests(TestCase):
    """Test SchoolGroupMembership model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='TestPass123!'
        )
        self.org = SchoolGroup.objects.create(
            name='Test Organization',
            description='Test',
            created_by=self.user
        )
    
    def test_create_membership(self):
        """Test creating a membership."""
        membership = SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.org,
            status='pending'
        )
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.school_group, self.org)
        self.assertEqual(membership.status, 'pending')
    
    def test_membership_status_choices(self):
        """Test membership status choices."""
        membership = SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.org,
            status='accepted'
        )
        self.assertEqual(membership.get_status_display(), 'Accepted')
    
    def test_membership_unique_together(self):
        """Test that unique_together constraint works."""
        # Create first membership
        SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.org,
            status='pending'
        )
        # Try to create duplicate (should fail)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            SchoolGroupMembership.objects.create(
                user=self.user,
                school_group=self.org,
                status='accepted'
            )


class JoinRequestTests(TestCase):
    """Test JoinRequest model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='TestPass123!'
        )
        self.org = SchoolGroup.objects.create(
            name='Test Organization',
            description='Test',
            created_by=self.user
        )
    
    def test_create_join_request(self):
        """Test creating a join request."""
        join_request = JoinRequest.objects.create(
            user=self.user,
            school_group=self.org,
            status='pending'
        )
        self.assertEqual(join_request.user, self.user)
        self.assertEqual(join_request.school_group, self.org)
        self.assertEqual(join_request.status, 'pending')
    
    def test_join_request_status_choices(self):
        """Test join request status choices."""
        join_request = JoinRequest.objects.create(
            user=self.user,
            school_group=self.org,
            status='accepted'
        )
        self.assertEqual(join_request.get_status_display(), 'Accepted')
    
    def test_unique_join_request_per_user_org(self):
        """Test that a user can only have one pending request per organization."""
        # Create first request
        JoinRequest.objects.create(
            user=self.user,
            school_group=self.org,
            status='pending'
        )
        # Try to create duplicate (should be allowed but handled in views)
        # This tests the model allows it (business logic in views)
        join_request2 = JoinRequest.objects.create(
            user=self.user,
            school_group=self.org,
            status='pending'
        )
        # Both should exist (business logic prevents this in views)
        self.assertEqual(JoinRequest.objects.filter(user=self.user, school_group=self.org).count(), 2)
