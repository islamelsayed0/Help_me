"""
Superadmin-facing audit log views.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime, timedelta
import csv

from .models import AuditLog
from accounts.decorators import superadmin_required
from accounts.utils import get_user_school_group


@login_required
@superadmin_required
def audit_log_list_view(request):
    """Superadmin audit log list showing all logs across all organizations."""
    user = request.user
    
    # Get all audit logs
    logs = AuditLog.objects.all().select_related('actor', 'school_group').order_by('-created_at')
    
    # Filter by action type
    action_filter = request.GET.get('action_type')
    if action_filter and action_filter in [choice[0] for choice in AuditLog.ACTION_TYPE_CHOICES]:
        logs = logs.filter(action_type=action_filter)
    
    # Filter by actor (user)
    actor_filter = request.GET.get('actor')
    if actor_filter:
        logs = logs.filter(actor__email__icontains=actor_filter)
    
    # Filter by school group
    school_group_filter = request.GET.get('school_group')
    if school_group_filter:
        logs = logs.filter(school_group__name__icontains=school_group_filter)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            date_from_dt = timezone.make_aware(date_from_dt)
            logs = logs.filter(created_at__gte=date_from_dt)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_dt = timezone.make_aware(date_to_dt) + timedelta(days=1)
            logs = logs.filter(created_at__lt=date_to_dt)
        except ValueError:
            pass
    
    # Search by description
    search_query = request.GET.get('search', '')
    if search_query:
        logs = logs.filter(description__icontains=search_query)
    
    # Pagination (simple, limit to 100 per page)
    logs = logs[:100]
    
    context = {
        'logs': logs,
        'action_filter': action_filter,
        'actor_filter': actor_filter,
        'school_group_filter': school_group_filter,
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
        'action_types': AuditLog.ACTION_TYPE_CHOICES,
    }
    
    return render(request, 'audit/admin/audit_log_list.html', context)


@login_required
@superadmin_required
def audit_log_export_view(request):
    """Export audit logs to CSV."""
    user = request.user
    
    # Get all audit logs with same filters as list view
    logs = AuditLog.objects.all().select_related('actor', 'school_group').order_by('-created_at')
    
    # Apply filters (same as list view)
    action_filter = request.GET.get('action_type')
    if action_filter and action_filter in [choice[0] for choice in AuditLog.ACTION_TYPE_CHOICES]:
        logs = logs.filter(action_type=action_filter)
    
    actor_filter = request.GET.get('actor')
    if actor_filter:
        logs = logs.filter(actor__email__icontains=actor_filter)
    
    school_group_filter = request.GET.get('school_group')
    if school_group_filter:
        logs = logs.filter(school_group__name__icontains=school_group_filter)
    
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        try:
            date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
            date_from_dt = timezone.make_aware(date_from_dt)
            logs = logs.filter(created_at__gte=date_from_dt)
        except ValueError:
            pass
    if date_to:
        try:
            date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
            date_to_dt = timezone.make_aware(date_to_dt) + timedelta(days=1)
            logs = logs.filter(created_at__lt=date_to_dt)
        except ValueError:
            pass
    
    search_query = request.GET.get('search', '')
    if search_query:
        logs = logs.filter(description__icontains=search_query)
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID',
        'Created At',
        'Actor',
        'Action Type',
        'Resource Type',
        'Resource ID',
        'School Group',
        'Description',
        'Metadata'
    ])
    
    for log in logs:
        writer.writerow([
            log.id,
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            log.actor.email if log.actor else 'System',
            log.get_action_type_display(),
            log.resource_type,
            log.resource_id,
            log.school_group.name if log.school_group else 'Global',
            log.description,
            str(log.metadata)
        ])
    
    return response
