from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from schoolgroups.models import SchoolGroup, SchoolGroupMembership
from .models import Chat, ChatMessage

User = get_user_model()


class ChatModelTests(TestCase):
    """Test Chat model functionality."""
    
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
        SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.org,
            status='accepted'
        )
    
    def test_create_chat(self):
        """Test creating a chat."""
        chat = Chat.objects.create(
            user=self.user,
            school_group=self.org,
            status='active'
        )
        self.assertEqual(chat.user, self.user)
        self.assertEqual(chat.school_group, self.org)
        self.assertEqual(chat.status, 'active')
    
    def test_chat_status_choices(self):
        """Test chat status choices."""
        chat = Chat.objects.create(
            user=self.user,
            school_group=self.org,
            status='resolved'
        )
        self.assertEqual(chat.get_status_display(), 'Resolved')
    
    def test_chat_str(self):
        """Test chat string representation."""
        chat = Chat.objects.create(
            user=self.user,
            school_group=self.org
        )
        chat_str = str(chat)
        self.assertIn('Chat', chat_str)
        self.assertIn(str(self.user.email), chat_str)
        self.assertIn('active', chat_str)  # Default status


class ChatMessageTests(TestCase):
    """Test ChatMessage model."""
    
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
    
    def test_create_user_message(self):
        """Test creating a user message."""
        message = ChatMessage.objects.create(
            chat=self.chat,
            sender=self.user,
            sender_type='user',
            content='Test message'
        )
        self.assertEqual(message.chat, self.chat)
        self.assertEqual(message.sender, self.user)
        self.assertEqual(message.sender_type, 'user')
        self.assertEqual(message.content, 'Test message')
        self.assertFalse(message.is_read)
    
    def test_create_ai_message(self):
        """Test creating an AI message."""
        message = ChatMessage.objects.create(
            chat=self.chat,
            sender=None,
            sender_type='ai',
            content='AI response'
        )
        self.assertEqual(message.sender_type, 'ai')
        self.assertIsNone(message.sender)
    
    def test_mark_as_read(self):
        """Test marking message as read."""
        message = ChatMessage.objects.create(
            chat=self.chat,
            sender=self.user,
            sender_type='user',
            content='Test'
        )
        self.assertFalse(message.is_read)
        message.mark_as_read()
        self.assertTrue(message.is_read)


class ChatViewTests(TestCase):
    """Test chat views."""
    
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
        self.client.login(username='user', password='TestPass123!')
    
    def test_chat_list_view(self):
        """Test chat list view."""
        response = self.client.get(reverse('chats:chat_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_create_chat_view(self):
        """Test create chat view."""
        response = self.client.get(reverse('chats:create_chat'))
        self.assertEqual(response.status_code, 200)
    
    def test_create_chat_post(self):
        """Test creating a chat via POST."""
        data = {
            'initial_message': 'Hello, I need help'
        }
        response = self.client.post(reverse('chats:create_chat'), data)
        self.assertEqual(response.status_code, 302)  # Should redirect
        # Check chat was created
        self.assertTrue(Chat.objects.filter(user=self.user).exists())
