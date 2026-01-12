"""
URL patterns for audit log views.
"""
from django.urls import path
from . import admin_views

app_name = 'audit'

urlpatterns = [
    # Superadmin routes
    path('superadmin/auditlogs/', admin_views.audit_log_list_view, name='audit_log_list'),
    path('superadmin/auditlogs/export/', admin_views.audit_log_export_view, name='audit_log_export'),
]
