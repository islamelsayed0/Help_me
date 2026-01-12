from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from schoolgroups.models import SchoolGroup, SchoolGroupMembership
from chats.models import Chat
from .models import Ticket

User = get_user_model()


class TicketModelTests(TestCase):
    """Test Ticket model functionality."""
    
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
        self.chat = Chat.objects.create(
            user=self.user,
            school_group=self.org
        )
    
    def test_create_ticket(self):
        """Test creating a ticket."""
        ticket = Ticket.objects.create(
            chat=self.chat,
            user=self.user,
            school_group=self.org,
            title='Test Ticket',
            description='Test Description',
            status='open',
            priority='medium'
        )
        self.assertEqual(ticket.user, self.user)
        self.assertEqual(ticket.school_group, self.org)
        self.assertEqual(ticket.status, 'open')
        self.assertEqual(ticket.priority, 'medium')
    
    def test_ticket_status_choices(self):
        """Test ticket status choices."""
        ticket = Ticket.objects.create(
            chat=self.chat,
            user=self.user,
            school_group=self.org,
            title='Test',
            status='in_progress'
        )
        self.assertEqual(ticket.get_status_display(), 'In Progress')
    
    def test_ticket_priority_choices(self):
        """Test ticket priority choices."""
        ticket = Ticket.objects.create(
            chat=self.chat,
            user=self.user,
            school_group=self.org,
            title='Test',
            priority='high'
        )
        self.assertEqual(ticket.get_priority_display(), 'High')
    
    def test_ticket_assign(self):
        """Test assigning a ticket."""
        admin = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='TestPass123!'
        )
        ticket = Ticket.objects.create(
            chat=self.chat,
            user=self.user,
            school_group=self.org,
            title='Test',
            status='open'
        )
        ticket.assign(admin)
        self.assertEqual(ticket.assigned_to, admin)
        self.assertEqual(ticket.status, 'in_progress')  # Status changes to in_progress, not 'assigned'
    
    def test_ticket_resolve(self):
        """Test resolving a ticket."""
        ticket = Ticket.objects.create(
            chat=self.chat,
            user=self.user,
            school_group=self.org,
            title='Test',
            status='open'
        )
        ticket.resolve('Fixed the issue')
        self.assertEqual(ticket.status, 'resolved')
        self.assertEqual(ticket.resolution_notes, 'Fixed the issue')
        self.assertIsNotNone(ticket.resolved_at)
    
    def test_ticket_close(self):
        """Test closing a ticket."""
        ticket = Ticket.objects.create(
            chat=self.chat,
            user=self.user,
            school_group=self.org,
            title='Test',
            status='resolved'
        )
        ticket.close()
        self.assertEqual(ticket.status, 'closed')
        self.assertIsNotNone(ticket.closed_at)


class TicketViewTests(TestCase):
    """Test ticket views."""
    
    def setUp(self):
        self.client = Client()
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
        SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.org,
            status='accepted'
        )
        self.chat = Chat.objects.create(
            user=self.user,
            school_group=self.org
        )
        self.ticket = Ticket.objects.create(
            chat=self.chat,
            user=self.user,
            school_group=self.org,
            title='Test Ticket',
            description='Test Description',
            status='open'
        )
        self.client.login(username='user', password='TestPass123!')
    
    def test_ticket_list_view(self):
        """Test ticket list view."""
        response = self.client.get(reverse('tickets:ticket_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Ticket')
    
    def test_ticket_detail_view(self):
        """Test ticket detail view."""
        response = self.client.get(reverse('tickets:ticket_detail', args=[self.ticket.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Ticket')
        self.assertContains(response, 'Test Description')
