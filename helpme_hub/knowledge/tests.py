from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from schoolgroups.models import SchoolGroup, SchoolGroupMembership
from .models import Article

User = get_user_model()


class ArticleModelTests(TestCase):
    """Test Article model functionality."""
    
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
        SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.school_group,
            status='accepted'
        )
    
    def test_article_creation(self):
        """Test creating an article."""
        article = Article.objects.create(
            title='Test Article',
            content='This is a test article with enough content to pass validation.',
            author=self.user,
            school_group=self.school_group,
            status='draft'
        )
        self.assertEqual(article.title, 'Test Article')
        self.assertEqual(article.status, 'draft')
        self.assertEqual(article.author, self.user)
        self.assertEqual(article.school_group, self.school_group)
        self.assertEqual(article.view_count, 0)
        self.assertEqual(article.helpful_votes, 0)
    
    def test_article_publish(self):
        """Test publishing an article."""
        article = Article.objects.create(
            title='Test Article',
            content='This is a test article with enough content to pass validation.',
            author=self.user,
            school_group=self.school_group,
            status='draft'
        )
        self.assertIsNone(article.published_at)
        
        article.publish()
        article.refresh_from_db()
        
        self.assertEqual(article.status, 'published')
        self.assertIsNotNone(article.published_at)
    
    def test_article_unpublish(self):
        """Test unpublishing an article."""
        article = Article.objects.create(
            title='Test Article',
            content='This is a test article with enough content to pass validation.',
            author=self.user,
            school_group=self.school_group,
            status='published'
        )
        article.published_at = timezone.now()
        article.save()
        
        article.unpublish()
        article.refresh_from_db()
        
        self.assertEqual(article.status, 'draft')
    
    def test_increment_view_count(self):
        """Test incrementing view count."""
        article = Article.objects.create(
            title='Test Article',
            content='This is a test article with enough content to pass validation.',
            author=self.user,
            school_group=self.school_group
        )
        initial_count = article.view_count
        
        article.increment_view_count()
        article.refresh_from_db()
        
        self.assertEqual(article.view_count, initial_count + 1)
    
    def test_mark_helpful(self):
        """Test marking article as helpful."""
        article = Article.objects.create(
            title='Test Article',
            content='This is a test article with enough content to pass validation.',
            author=self.user,
            school_group=self.school_group
        )
        initial_votes = article.helpful_votes
        
        article.mark_helpful()
        article.refresh_from_db()
        
        self.assertEqual(article.helpful_votes, initial_votes + 1)
    
    def test_is_published(self):
        """Test is_published method."""
        draft_article = Article.objects.create(
            title='Draft Article',
            content='This is a draft article with enough content.',
            author=self.user,
            school_group=self.school_group,
            status='draft'
        )
        published_article = Article.objects.create(
            title='Published Article',
            content='This is a published article with enough content.',
            author=self.user,
            school_group=self.school_group,
            status='published'
        )
        
        self.assertFalse(draft_article.is_published())
        self.assertTrue(published_article.is_published())
    
    def test_is_global(self):
        """Test is_global method."""
        global_article = Article.objects.create(
            title='Global Article',
            content='This is a global article with enough content.',
            author=self.user,
            school_group=None
        )
        group_article = Article.objects.create(
            title='Group Article',
            content='This is a group article with enough content.',
            author=self.user,
            school_group=self.school_group
        )
        
        self.assertTrue(global_article.is_global())
        self.assertFalse(group_article.is_global())
    
    def test_get_excerpt(self):
        """Test get_excerpt method."""
        long_content = 'A' * 300
        article = Article.objects.create(
            title='Test Article',
            content=long_content,
            author=self.user,
            school_group=self.school_group
        )
        
        excerpt = article.get_excerpt(length=200)
        self.assertEqual(len(excerpt), 203)  # 200 + '...'
        self.assertTrue(excerpt.endswith('...'))
        
        short_content = 'Short content'
        article2 = Article.objects.create(
            title='Test Article 2',
            content=short_content,
            author=self.user,
            school_group=self.school_group
        )
        
        excerpt2 = article2.get_excerpt()
        self.assertEqual(excerpt2, short_content)
    
    def test_article_str(self):
        """Test article string representation."""
        article = Article.objects.create(
            title='Test Article',
            content='This is a test article with enough content.',
            author=self.user,
            school_group=self.school_group,
            status='draft'
        )
        self.assertIn('Test Article', str(article))
        self.assertIn('draft', str(article))


class ArticleViewTests(TestCase):
    """Test user-facing article views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.school_group = SchoolGroup.objects.create(
            name='Test School',
            created_by=self.user
        )
        SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.school_group,
            status='accepted'
        )
        self.article = Article.objects.create(
            title='Published Article',
            content='This is a published article with enough content to pass validation.',
            author=self.user,
            school_group=self.school_group,
            status='published'
        )
        self.article.publish()
    
    def test_article_list_view_requires_login(self):
        """Test that article list requires login."""
        response = self.client.get(reverse('knowledge:article_list'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_article_list_view_authenticated(self):
        """Test article list view for authenticated user."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('knowledge:article_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Published Article')
    
    def test_article_list_search(self):
        """Test article list search functionality."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('knowledge:article_list'), {'search': 'Published'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Published Article')
        
        response = self.client.get(reverse('knowledge:article_list'), {'search': 'Nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Published Article')
    
    def test_article_list_category_filter(self):
        """Test article list category filtering."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('knowledge:article_list'), {'category': 'general'})
        self.assertEqual(response.status_code, 200)
    
    def test_article_detail_view(self):
        """Test article detail view."""
        self.client.login(email='test@example.com', password='testpass123')
        response = self.client.get(reverse('knowledge:article_detail', args=[self.article.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Published Article')
        
        # Check that view count was incremented
        self.article.refresh_from_db()
        self.assertEqual(self.article.view_count, 1)
    
    def test_article_detail_increments_view_count(self):
        """Test that viewing an article increments view count."""
        self.client.login(email='test@example.com', password='testpass123')
        initial_count = self.article.view_count
        
        self.client.get(reverse('knowledge:article_detail', args=[self.article.id]))
        self.article.refresh_from_db()
        
        self.assertEqual(self.article.view_count, initial_count + 1)
    
    def test_mark_helpful_view(self):
        """Test marking article as helpful."""
        self.client.login(email='test@example.com', password='testpass123')
        initial_votes = self.article.helpful_votes
        
        response = self.client.post(reverse('knowledge:mark_helpful', args=[self.article.id]))
        self.assertEqual(response.status_code, 200)
        
        self.article.refresh_from_db()
        self.assertEqual(self.article.helpful_votes, initial_votes + 1)


class ArticleAdminViewTests(TestCase):
    """Test admin-facing article views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='admin@example.com',
            username='admin',
            password='adminpass123',
            role='admin'
        )
        self.school_group = SchoolGroup.objects.create(
            name='Test School',
            created_by=self.user
        )
        SchoolGroupMembership.objects.create(
            user=self.user,
            school_group=self.school_group,
            status='accepted'
        )
        self.article = Article.objects.create(
            title='Test Article',
            content='This is a test article with enough content to pass validation.',
            author=self.user,
            school_group=self.school_group,
            status='draft'
        )
    
    def test_admin_article_list_requires_admin(self):
        """Test that admin article list requires admin role."""
        regular_user = User.objects.create_user(
            email='user@example.com',
            username='user',
            password='userpass123',
            role='user'
        )
        SchoolGroupMembership.objects.create(
            user=regular_user,
            school_group=self.school_group,
            status='accepted'
        )
        
        self.client.login(email='user@example.com', password='userpass123')
        response = self.client.get(reverse('knowledge:admin_article_list'))
        self.assertNotEqual(response.status_code, 200)
    
    def test_admin_article_list_view(self):
        """Test admin article list view."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('knowledge:admin_article_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Article')
    
    def test_admin_article_create_view_get(self):
        """Test admin article create view GET."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('knowledge:admin_article_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_article_create_view_post(self):
        """Test admin article create view POST."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.post(reverse('knowledge:admin_article_create'), {
            'title': 'New Article',
            'content': 'This is a new article with enough content to pass validation.',
            'category': 'general',
            'status': 'draft',
            'tags': '["tag1", "tag2"]'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        
        # Verify article was created
        self.assertTrue(Article.objects.filter(title='New Article').exists())
    
    def test_admin_article_edit_view_get(self):
        """Test admin article edit view GET."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('knowledge:admin_article_edit', args=[self.article.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Article')
    
    def test_admin_article_edit_view_post(self):
        """Test admin article edit view POST."""
        self.client.login(email='admin@example.com', password='adminpass123')
        response = self.client.post(reverse('knowledge:admin_article_edit', args=[self.article.id]), {
            'title': 'Updated Article',
            'content': 'This is an updated article with enough content to pass validation.',
            'category': 'technical',
            'status': 'published',
            'tags': '["updated", "tag"]'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after update
        
        # Verify article was updated
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Updated Article')
        self.assertEqual(self.article.category, 'technical')
        self.assertEqual(self.article.status, 'published')
    
    def test_admin_article_delete_view(self):
        """Test admin article delete view."""
        self.client.login(email='admin@example.com', password='adminpass123')
        article_id = self.article.id
        
        response = self.client.post(reverse('knowledge:admin_article_delete', args=[article_id]))
        self.assertEqual(response.status_code, 302)  # Redirect after deletion
        
        # Verify article was deleted
        self.assertFalse(Article.objects.filter(id=article_id).exists())
