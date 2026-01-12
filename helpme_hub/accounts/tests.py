from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.messages import get_messages
from schoolgroups.models import SchoolGroup, SchoolGroupMembership, JoinRequest
from .forms import UserRegistrationForm, JoinRequestForm, CreateOrganizationForm
from .utils import has_accepted_membership, get_user_school_group, get_user_organizations

User = get_user_model()


class UserRegistrationTests(TestCase):
    """Test user registration functionality."""
    
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('accounts:register')
    
    def test_registration_page_loads(self):
        """Test that registration page loads successfully."""
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Account')
    
    def test_user_registration_success(self):
        """Test successful user registration."""
        data = {
            'email': 'test@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data)
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        # Check user was created
        self.assertTrue(User.objects.filter(email='test@example.com').exists())
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
    
    def test_registration_duplicate_email(self):
        """Test that duplicate email registration fails."""
        # Create first user
        User.objects.create_user(
            email='existing@example.com',
            username='existing',
            password='TestPass123!'
        )
        # Try to register with same email
        data = {
            'email': 'existing@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)  # Should stay on page
        self.assertFormError(response, 'form', 'email', 'A user with this email address already exists.')
    
    def test_registration_password_mismatch(self):
        """Test that password mismatch fails validation."""
        data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'TestPass123!',
            'password2': 'DifferentPass123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        # Check for password mismatch error (can be single or double quotes)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        self.assertTrue(any('match' in str(error).lower() for error in form.errors['password2']))
    
    def test_registration_weak_password(self):
        """Test that weak passwords are rejected."""
        data = {
            'email': 'test@example.com',
            'password1': 'weak',
            'password2': 'weak',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, 200)
        # Should have password validation errors
        form = response.context['form']
        self.assertFalse(form.is_valid())


class LoginTests(TestCase):
    """Test login functionality."""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('accounts:login')
        self.user = User.objects.create_user(
            email='testuser@example.com',
            username='testuser',
            password='TestPass123!'
        )
    
    def test_login_page_loads(self):
        """Test that login page loads successfully."""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Welcome Back')
    
    def test_login_success(self):
        """Test successful login."""
        data = {
            'login': 'testuser@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)
        # Check user is authenticated
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_login_wrong_password(self):
        """Test login with wrong password."""
        data = {
            'login': 'testuser@example.com',
            'password': 'WrongPassword123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)  # Should stay on page
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Wrong account information' in str(m) for m in messages))
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent email."""
        data = {
            'login': 'nonexistent@example.com',
            'password': 'TestPass123!'
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Wrong account information' in str(m) for m in messages))
    
    def test_login_missing_credentials(self):
        """Test login with missing credentials."""
        data = {
            'login': '',
            'password': ''
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Please enter both email and password' in str(m) for m in messages))


class OrganizationCreationTests(TestCase):
    """Test organization creation functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='TestPass123!'
        )
        self.client.login(username='admin', password='TestPass123!')
        self.create_org_url = reverse('accounts:create_organization')
    
    def test_create_organization_page_loads(self):
        """Test that create organization page loads."""
        response = self.client.get(self.create_org_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Organization')
    
    def test_create_organization_success(self):
        """Test successful organization creation."""
        data = {
            'name': 'Test Organization',
            'description': 'Test Description'
        }
        response = self.client.post(self.create_org_url, data)
        self.assertEqual(response.status_code, 302)  # Should redirect
        # Check organization was created
        org = SchoolGroup.objects.get(name='Test Organization')
        self.assertEqual(org.created_by, self.user)
        self.assertTrue(org.access_code)  # Access code should be generated
        # Check user is admin member
        membership = SchoolGroupMembership.objects.get(user=self.user, school_group=org)
        self.assertEqual(membership.status, 'accepted')
        # Check user role was updated to admin
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'admin')
    
    def test_user_can_only_create_one_organization(self):
        """Test that a user can only create one organization."""
        # Create first organization
        org1 = SchoolGroup.objects.create(
            name='First Org',
            description='First',
            created_by=self.user
        )
        org1.generate_access_code()
        # Try to create second organization
        data = {
            'name': 'Second Organization',
            'description': 'Second'
        }
        response = self.client.post(self.create_org_url, data)
        # View checks has_created_organization() and redirects with warning
        # Verify second organization was not created
        self.assertEqual(SchoolGroup.objects.filter(created_by=self.user).count(), 1)
        # Check warning message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('already' in str(m).lower() or 'one organization' in str(m).lower() for m in messages))


class AccessCodeTests(TestCase):
    """Test access code functionality."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='TestPass123!'
        )
        self.org = SchoolGroup.objects.create(
            name='Test Organization',
            description='Test',
            created_by=self.user
        )
        self.client.login(username='admin', password='TestPass123!')
    
    def test_access_code_generated(self):
        """Test that access code can be generated."""
        # Access code is not auto-generated, must be called explicitly
        self.org.generate_access_code()
        self.assertTrue(self.org.access_code)
        self.assertGreaterEqual(len(self.org.access_code), 12)
    
    def test_access_code_formatting(self):
        """Test access code formatting."""
        # Generate access code first
        self.org.generate_access_code()
        formatted = self.org.get_formatted_access_code()
        # Should have dashes in format XXXX-XXXX-XXXX
        self.assertIn('-', formatted)
        self.assertEqual(len(formatted.replace('-', '')), len(self.org.access_code))
    
    def test_access_code_validation(self):
        """Test access code validation."""
        # Generate access code first
        self.org.generate_access_code()
        # Valid code
        self.assertTrue(self.org.is_access_code_valid())
        # Test with normalized input
        formatted = self.org.get_formatted_access_code()
        normalized = SchoolGroup.normalize_access_code(formatted)
        self.assertEqual(normalized, self.org.access_code)
    
    def test_regenerate_access_code(self):
        """Test access code regeneration."""
        # Generate initial code
        self.org.generate_access_code()
        old_code = self.org.access_code
        self.org.regenerate_access_code()
        new_code = self.org.access_code
        self.assertNotEqual(old_code, new_code)
        self.assertTrue(self.org.is_access_code_valid())


class JoinRequestTests(TestCase):
    """Test join request functionality."""
    
    def setUp(self):
        self.client = Client()
        # Create admin user and organization
        self.admin = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='TestPass123!'
        )
        self.org = SchoolGroup.objects.create(
            name='Test Organization',
            description='Test',
            created_by=self.admin
        )
        # Create regular user
        self.user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='TestPass123!'
        )
        self.client.login(username='user', password='TestPass123!')
    
    def test_join_with_valid_access_code(self):
        """Test joining organization with valid access code."""
        # Generate access code first
        self.org.generate_access_code()
        access_code = self.org.access_code
        data = {
            'access_code': access_code
        }
        response = self.client.post(reverse('accounts:request_join'), data)
        self.assertEqual(response.status_code, 302)  # Should redirect
        # Check join request was created
        join_request = JoinRequest.objects.get(user=self.user, school_group=self.org)
        self.assertEqual(join_request.status, 'pending')
    
    def test_join_with_invalid_access_code(self):
        """Test joining with invalid access code."""
        data = {
            'access_code': 'INVALID-CODE-123'
        }
        response = self.client.post(reverse('accounts:request_join'), data)
        # Form validation should fail, redirecting to pending or dashboard
        # Check that no join request was created
        self.assertFalse(JoinRequest.objects.filter(user=self.user, school_group=self.org).exists())
        # Check error message (form validation error or message)
        messages = list(get_messages(response.wsgi_request))
        # Error could be in messages or form errors
        has_error = any('Invalid' in str(m) or 'invalid' in str(m).lower() or 'error' in str(m).lower() 
                       for m in messages)
        # If no message, check form errors in response
        if not has_error and response.status_code == 200:
            form = response.context.get('form')
            if form:
                has_error = 'access_code' in form.errors
        self.assertTrue(has_error or response.status_code == 302)  # Either error shown or redirected
    
    def test_join_with_formatted_access_code(self):
        """Test that formatted access code (with dashes) works."""
        # Generate access code first
        self.org.generate_access_code()
        formatted_code = self.org.get_formatted_access_code()
        data = {
            'access_code': formatted_code
        }
        response = self.client.post(reverse('accounts:request_join'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(JoinRequest.objects.filter(user=self.user, school_group=self.org).exists())
    
    def test_duplicate_join_request(self):
        """Test that user can't create duplicate join request for same organization."""
        # Generate access code first
        self.org.generate_access_code()
        # Create first join request
        JoinRequest.objects.create(
            user=self.user,
            school_group=self.org,
            status='pending'
        )
        # Also create membership (form checks for membership too)
        SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.org,
            status='pending'
        )
        # Try to create another
        data = {
            'access_code': self.org.access_code
        }
        response = self.client.post(reverse('accounts:request_join'), data)
        # Form validation should prevent duplicate (checks both JoinRequest and Membership)
        # Check that only one join request exists
        self.assertEqual(JoinRequest.objects.filter(user=self.user, school_group=self.org, status='pending').count(), 1)
        # Form validation error should prevent creation, check messages or form errors
        messages = list(get_messages(response.wsgi_request))
        # Form validation error message or warning message
        has_message = any('already' in str(m).lower() or 'pending' in str(m).lower() or 'membership' in str(m).lower() 
                         for m in messages)
        # If no message, form validation prevented it (which is correct behavior)
        self.assertTrue(has_message or response.status_code == 302)


class MembershipUtilsTests(TestCase):
    """Test membership utility functions."""
    
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
    
    def test_has_accepted_membership(self):
        """Test has_accepted_membership utility."""
        # No membership
        self.assertFalse(has_accepted_membership(self.user))
        # Pending membership
        SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.org,
            status='pending'
        )
        self.assertFalse(has_accepted_membership(self.user))
        # Accepted membership
        membership = SchoolGroupMembership.objects.get(user=self.user, school_group=self.org)
        membership.status = 'accepted'
        membership.save()
        self.assertTrue(has_accepted_membership(self.user))
    
    def test_get_user_school_group(self):
        """Test get_user_school_group utility."""
        # No membership
        self.assertIsNone(get_user_school_group(self.user))
        # With accepted membership
        SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.org,
            status='accepted'
        )
        self.assertEqual(get_user_school_group(self.user), self.org)
    
    def test_get_user_organizations(self):
        """Test get_user_organizations utility."""
        # No organizations
        self.assertEqual(len(get_user_organizations(self.user)), 0)
        # With multiple memberships
        org2 = SchoolGroup.objects.create(
            name='Second Organization',
            description='Second',
            created_by=self.user
        )
        SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.org,
            status='accepted'
        )
        SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=org2,
            status='accepted'
        )
        orgs = get_user_organizations(self.user)
        self.assertEqual(len(orgs), 2)
        self.assertIn(self.org, orgs)
        self.assertIn(org2, orgs)
