from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from schoolgroups.models import SchoolGroup, SchoolGroupMembership
from .models import AuditLog
from audit.utils import log_action

User = get_user_model()


class AuditLogModelTests(TestCase):
    """Test AuditLog model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.school_group = SchoolGroup.objects.create(
            name='Test School',
            created_by=self.user
        )
    
    def test_audit_log_creation(self):
        """Test creating an audit log entry."""
        log = AuditLog.objects.create(
            actor=self.user,
            school_group=self.school_group,
            action_type='join_request_created',
            resource_type='JoinRequest',
            resource_id=1,
            description='Test audit log entry'
        )
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.school_group, self.school_group)
        self.assertEqual(log.action_type, 'join_request_created')
        self.assertEqual(log.resource_type, 'JoinRequest')
        self.assertEqual(log.resource_id, 1)
        self.assertIsNotNone(log.created_at)
    
    def test_audit_log_without_actor(self):
        """Test creating an audit log without an actor (system action)."""
        log = AuditLog.objects.create(
            actor=None,
            school_group=None,
            action_type='settings_changed',
            resource_type='System',
            resource_id=0,
            description='System configuration changed'
        )
        self.assertIsNone(log.actor)
        self.assertIsNone(log.school_group)
    
    def test_audit_log_str(self):
        """Test audit log string representation."""
        log = AuditLog.objects.create(
            actor=self.user,
            school_group=self.school_group,
            action_type='role_changed',
            resource_type='User',
            resource_id=1,
            description='User role changed'
        )
        str_repr = str(log)
        self.assertIn(self.user.email, str_repr)
        self.assertIn('Role Changed', str_repr)
        self.assertIn('User', str_repr)
    
    def test_audit_log_metadata(self):
        """Test audit log with metadata."""
        metadata = {'old_role': 'user', 'new_role': 'admin'}
        log = AuditLog.objects.create(
            actor=self.user,
            school_group=self.school_group,
            action_type='role_changed',
            resource_type='User',
            resource_id=1,
            description='User role changed',
            metadata=metadata
        )
        self.assertEqual(log.metadata, metadata)
    
    def test_audit_log_ordering(self):
        """Test that audit logs are ordered by created_at descending."""
        log1 = AuditLog.objects.create(
            actor=self.user,
            action_type='join_request_created',
            resource_type='JoinRequest',
            resource_id=1,
            description='First log'
        )
        # Small delay to ensure different timestamps
        import time
        time.sleep(0.01)
        log2 = AuditLog.objects.create(
            actor=self.user,
            action_type='join_request_created',
            resource_type='JoinRequest',
            resource_id=2,
            description='Second log'
        )
        
        logs = AuditLog.objects.all()
        self.assertEqual(logs[0], log2)  # Most recent first
        self.assertEqual(logs[1], log1)


class AuditLogViewTests(TestCase):
    """Test superadmin audit log views."""
    
    def setUp(self):
        self.client = Client()
        self.superadmin = User.objects.create_user(
            email='superadmin@example.com',
            username='superadmin',
            password='adminpass123',
            role='superadmin'
        )
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='userpass123',
            role='user'
        )
        self.school_group = SchoolGroup.objects.create(
            name='Test School',
            created_by=self.user
        )
        self.audit_log = AuditLog.objects.create(
            actor=self.user,
            school_group=self.school_group,
            action_type='join_request_created',
            resource_type='JoinRequest',
            resource_id=1,
            description='Test audit log entry'
        )
    
    def test_audit_log_list_requires_superadmin(self):
        """Test that audit log list requires superadmin role."""
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('audit:audit_log_list'))
        self.assertNotEqual(response.status_code, 200)
    
    def test_audit_log_list_view(self):
        """Test audit log list view for superadmin."""
        self.client.login(email='superadmin@example.com', password='adminpass123')
        response = self.client.get(reverse('audit:audit_log_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test audit log entry')
    
    def test_audit_log_list_action_filter(self):
        """Test audit log list filtering by action type."""
        self.client.login(email='superadmin@example.com', password='adminpass123')
        response = self.client.get(reverse('audit:admin_audit_log_list'), {
            'action_type': 'join_request_created'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test audit log entry')
        
        response = self.client.get(reverse('audit:admin_audit_log_list'), {
            'action_type': 'role_changed'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Test audit log entry')
    
    def test_audit_log_list_actor_filter(self):
        """Test audit log list filtering by actor."""
        self.client.login(email='superadmin@example.com', password='adminpass123')
        response = self.client.get(reverse('audit:admin_audit_log_list'), {
            'actor': 'user@example.com'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test audit log entry')
    
    def test_audit_log_list_search(self):
        """Test audit log list search functionality."""
        self.client.login(email='superadmin@example.com', password='adminpass123')
        response = self.client.get(reverse('audit:admin_audit_log_list'), {
            'search': 'Test audit'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test audit log entry')
        
        response = self.client.get(reverse('audit:admin_audit_log_list'), {
            'search': 'Nonexistent'
        })
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Test audit log entry')
    
    def test_audit_log_export_view(self):
        """Test audit log CSV export."""
        self.client.login(email='superadmin@example.com', password='adminpass123')
        response = self.client.get(reverse('audit:audit_log_export'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="audit_logs.csv"', response['Content-Disposition'])
        self.assertIn(b'Test audit log entry', response.content)
    
    def test_audit_log_export_with_filters(self):
        """Test audit log export with filters."""
        self.client.login(email='superadmin@example.com', password='adminpass123')
        response = self.client.get(reverse('audit:audit_log_export'), {
            'action_type': 'join_request_created'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test audit log entry', response.content)


class AuditLogIntegrationTests(TestCase):
    """Test audit logging integration across app actions."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.school_group = SchoolGroup.objects.create(
            name='Test School',
            created_by=self.user
        )
    
    def test_log_action_utility(self):
        """Test the log_action utility function."""
        from audit.utils import log_action
        
        log_action(
            actor=self.user,
            action_type='join_request_created',
            resource_type='JoinRequest',
            resource_id=1,
            description='Test action logged',
            school_group=self.school_group
        )
        
        log = AuditLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.actor, self.user)
        self.assertEqual(log.school_group, self.school_group)
        self.assertEqual(log.action_type, 'join_request_created')
        self.assertEqual(log.description, 'Test action logged')
        self.assertEqual(log.resource_type, 'JoinRequest')
        self.assertEqual(log.resource_id, 1)
    
    def test_log_action_with_resource(self):
        """Test log_action with a resource object."""
        from audit.utils import log_action
        
        # Create a test resource (using SchoolGroup as example)
        log_action(
            actor=self.user,
            action_type='settings_changed',
            resource_type='SchoolGroup',
            resource_id=self.school_group.id,
            description='School group settings changed',
            school_group=self.school_group
        )
        
        log = AuditLog.objects.first()
        self.assertIsNotNone(log)
        self.assertEqual(log.resource_type, 'SchoolGroup')
        self.assertEqual(log.resource_id, self.school_group.id)
    
    def test_log_action_without_school_group(self):
        """Test log_action without a school group (global action)."""
        from audit.utils import log_action
        
        log_action(
            actor=self.user,
            action_type='settings_changed',
            resource_type='System',
            resource_id=0,
            description='Global system settings changed',
            school_group=None
        )
        
        log = AuditLog.objects.first()
        self.assertIsNotNone(log)
        self.assertIsNone(log.school_group)
    
    def test_multiple_audit_logs(self):
        """Test creating multiple audit logs."""
        from audit.utils import log_action
        
        log_action(
            actor=self.user,
            action_type='join_request_created',
            resource_type='JoinRequest',
            resource_id=1,
            description='First action',
            school_group=self.school_group
        )
        log_action(
            actor=self.user,
            action_type='role_changed',
            resource_type='User',
            resource_id=1,
            description='Second action',
            school_group=self.school_group
        )
        
        logs = AuditLog.objects.all()
        self.assertEqual(logs.count(), 2)
        # Verify ordering (most recent first)
        self.assertEqual(logs[0].action_type, 'role_changed')
        self.assertEqual(logs[1].action_type, 'join_request_created')
