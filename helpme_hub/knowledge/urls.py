"""
URL patterns for knowledge base views.
"""
from django.urls import path
from . import views
from . import admin_views

app_name = 'knowledge'

urlpatterns = [
    # User routes
    path('', views.article_list_view, name='article_list'),
    path('<int:article_id>/', views.article_detail_view, name='article_detail'),
    path('<int:article_id>/helpful/', views.mark_helpful_view, name='mark_helpful'),
    
    # Admin routes
    path('admin/', admin_views.admin_article_list_view, name='admin_article_list'),
    path('admin/create/', admin_views.admin_article_create_view, name='admin_article_create'),
    path('admin/<int:article_id>/edit/', admin_views.admin_article_edit_view, name='admin_article_edit'),
    path('admin/<int:article_id>/delete/', admin_views.admin_article_delete_view, name='admin_article_delete'),
    path('admin/<int:article_id>/publish/', admin_views.admin_article_publish_view, name='admin_article_publish'),
]
