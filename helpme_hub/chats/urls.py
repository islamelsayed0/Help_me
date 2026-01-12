"""
URL patterns for chat views.
"""
from django.urls import path
from . import views
from . import admin_views

app_name = 'chats'

urlpatterns = [
    # User routes
    path('', views.chat_list_view, name='chat_list'),
    path('create/', views.create_chat_view, name='create_chat'),
    path('quick-help/', views.quick_help_view, name='quick_help'),
    path('<int:chat_id>/', views.chat_detail_view, name='chat_detail'),
    path('<int:chat_id>/send/', views.send_message_view, name='send_message'),
    path('<int:chat_id>/escalate/', views.escalate_chat_view, name='escalate_chat'),
    path('<int:chat_id>/mark-read/', views.mark_messages_read_view, name='mark_read'),
    path('<int:chat_id>/poll/', views.poll_messages_view, name='poll_messages'),
    
    # Admin routes
    path('admin/inbox/', admin_views.admin_chat_inbox_view, name='admin_inbox'),
    path('admin/<int:chat_id>/', admin_views.admin_chat_detail_view, name='admin_chat_detail'),
    path('admin/<int:chat_id>/assign/', admin_views.assign_chat_view, name='assign_chat'),
    path('admin/<int:chat_id>/unassign/', admin_views.unassign_chat_view, name='unassign_chat'),
    path('admin/<int:chat_id>/send/', admin_views.send_admin_message_view, name='send_admin_message'),
    path('admin/<int:chat_id>/resolve/', admin_views.resolve_chat_view, name='resolve_chat'),
    path('admin/<int:chat_id>/close/', admin_views.close_chat_view, name='close_chat'),
    path('admin/<int:chat_id>/poll/', admin_views.admin_poll_messages_view, name='admin_poll_messages'),
]
