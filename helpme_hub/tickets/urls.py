"""
URL patterns for ticket views.
"""
from django.urls import path
from . import views
from . import admin_views

app_name = 'tickets'

urlpatterns = [
    # User routes
    path('', views.ticket_list_view, name='ticket_list'),
    path('create/', views.create_ticket_view, name='create_ticket'),
    path('<int:ticket_id>/', views.ticket_detail_view, name='ticket_detail'),
    
    # Admin routes
    path('admin/board/', admin_views.admin_ticket_board_view, name='admin_board'),
    path('admin/<int:ticket_id>/', admin_views.admin_ticket_detail_view, name='admin_ticket_detail'),
    path('admin/<int:ticket_id>/assign/', admin_views.assign_ticket_view, name='assign_ticket'),
    path('admin/<int:ticket_id>/update-status/', admin_views.update_ticket_status_view, name='update_status'),
    path('admin/<int:ticket_id>/resolve/', admin_views.add_resolution_notes_view, name='add_resolution'),
    path('admin/<int:ticket_id>/close/', admin_views.close_ticket_view, name='close_ticket'),
]
