"""
Admin views for managing join requests and organization memberships.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.utils import timezone
import logging
from .decorators import role_required, superadmin_required
from schoolgroups.models import JoinRequest, SchoolGroupMembership, SchoolGroup
from .utils import get_user_school_group
from .models import User
from audit.utils import log_action

logger = logging.getLogger(__name__)


@login_required
@role_required(['admin', 'superadmin'])
def join_requests_list_view(request):
    """
    List all pending join requests for admin's organization.
    Admins see requests for their organization, superadmins see all requests.
    """
    user = request.user
    
    # Get admin's organization
    if user.is_superadmin():
        # Superadmins can see all join requests
        join_requests = JoinRequest.objects.filter(
            status='pending'
        ).select_related('user', 'school_group').order_by('-requested_at')
    else:
        # Regular admins see only requests for their organization
        admin_school_group = get_user_school_group(user)
        if not admin_school_group:
            messages.error(request, 'You must be a member of an organization to manage join requests.')
            return redirect('accounts:dashboard')
        
        join_requests = JoinRequest.objects.filter(
            school_group=admin_school_group,
            status='pending'
        ).select_related('user', 'school_group').order_by('-requested_at')
    
    # Get filter parameter
    status_filter = request.GET.get('status', 'pending')
    if status_filter != 'pending':
        join_requests = join_requests.filter(status=status_filter)
    
    context = {
        'join_requests': join_requests,
        'status_filter': status_filter,
        'pending_count': join_requests.filter(status='pending').count(),
    }
    
    return render(request, 'accounts/admin/join_requests_list.html', context)


@login_required
@role_required(['admin', 'superadmin'])
def join_request_detail_view(request, request_id):
    """
    View single join request details.
    """
    user = request.user
    
    # Get join request
    join_request = get_object_or_404(
        JoinRequest.objects.select_related('user', 'school_group', 'reviewed_by'),
        id=request_id
    )
    
    # Check permissions
    if not user.is_superadmin():
        admin_school_group = get_user_school_group(user)
        if not admin_school_group or join_request.school_group != admin_school_group:
            messages.error(request, 'You do not have permission to view this join request.')
            return redirect('accounts:admin_join_requests')
    
    # Get membership if exists
    membership = SchoolGroupMembership.objects.filter(
        user=join_request.user,
        school_group=join_request.school_group
    ).first()
    
    context = {
        'join_request': join_request,
        'membership': membership,
    }
    
    return render(request, 'accounts/admin/join_request_detail.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@require_http_methods(['POST'])
def accept_join_request_view(request, request_id):
    """
    Accept a join request.
    Updates JoinRequest and SchoolGroupMembership status to 'accepted'.
    """
    user = request.user
    
    # Get join request
    join_request = get_object_or_404(JoinRequest, id=request_id)
    
    # Check permissions
    if not user.is_superadmin():
        admin_school_group = get_user_school_group(user)
        if not admin_school_group or join_request.school_group != admin_school_group:
            messages.error(request, 'You do not have permission to accept this join request.')
            return redirect('accounts:admin_join_requests')
    
    # Check if already processed
    if join_request.status != 'pending':
        messages.warning(request, 'This join request has already been processed.')
        return redirect('accounts:admin_join_request_detail', request_id=request_id)
    
    # Accept the request
    join_request.accept(reviewed_by=user)
    
    # Log audit action
    from audit.utils import log_join_request_accepted
    log_join_request_accepted(user, join_request)
    
    # Send email notification
    try:
        from accounts.notifications import send_join_request_approved_email
        send_join_request_approved_email(join_request.user, join_request.school_group)
    except Exception as e:
        logger.error(f'Failed to send join request approved email: {str(e)}')
    
    messages.success(
        request,
        f'Join request from {join_request.user.email} has been accepted. '
        f'They are now a member of {join_request.school_group.name}.'
    )
    
    return redirect('accounts:admin_join_requests')


@login_required
@role_required(['admin', 'superadmin'])
@require_http_methods(['POST'])
def deny_join_request_view(request, request_id):
    """
    Deny a join request.
    Updates JoinRequest and SchoolGroupMembership status to 'denied'.
    """
    user = request.user
    
    # Get join request
    join_request = get_object_or_404(JoinRequest, id=request_id)
    
    # Check permissions
    if not user.is_superadmin():
        admin_school_group = get_user_school_group(user)
        if not admin_school_group or join_request.school_group != admin_school_group:
            messages.error(request, 'You do not have permission to deny this join request.')
            return redirect('accounts:admin_join_requests')
    
    # Check if already processed
    if join_request.status != 'pending':
        messages.warning(request, 'This join request has already been processed.')
        return redirect('accounts:admin_join_request_detail', request_id=request_id)
    
    # Get notes from form
    notes = request.POST.get('notes', '').strip()
    
    # Deny the request
    join_request.deny(reviewed_by=user, notes=notes)
    
    # Log audit action
    from audit.utils import log_join_request_denied
    log_join_request_denied(user, join_request)
    
    # Send email notification
    try:
        from accounts.notifications import send_join_request_denied_email
        send_join_request_denied_email(join_request.user, join_request.school_group, notes)
    except Exception as e:
        logger.error(f'Failed to send join request denied email: {str(e)}')
    
    messages.info(
        request,
        f'Join request from {join_request.user.email} has been denied.'
    )
    
    return redirect('accounts:admin_join_requests')


@login_required
@role_required(['admin', 'superadmin'])
def view_access_code_view(request):
    """
    Display current access code for admin's organization.
    Shows code, generation date, expiry date, and allows regeneration.
    """
    user = request.user
    
    if user.is_superadmin():
        org_id = (request.GET.get('organization_id') or '').strip()
        if not org_id:
            school_groups = SchoolGroup.objects.order_by('name')[:500]
            return render(
                request,
                'accounts/admin/access_code_pick_org.html',
                {'school_groups': school_groups},
            )
        try:
            organization = SchoolGroup.objects.get(pk=int(org_id))
        except (ValueError, SchoolGroup.DoesNotExist):
            messages.error(request, 'Organization not found.')
            return redirect('accounts:superadmin_schoolgroups')
    else:
        organization = get_user_school_group(user)
        if not organization:
            messages.error(request, 'You must be a member of an organization to view access codes.')
            return redirect('accounts:dashboard')
    
    # Calculate days until expiry
    days_until_expiry = None
    if organization.access_code_expires_at:
        delta = organization.access_code_expires_at - timezone.now()
        days_until_expiry = delta.days
    
    # Get formatted access code for display
    formatted_code = organization.get_formatted_access_code() if organization.access_code else None
    
    context = {
        'organization': organization,
        'access_code': formatted_code,
        'generated_at': organization.access_code_generated_at,
        'expires_at': organization.access_code_expires_at,
        'days_until_expiry': days_until_expiry,
        'is_valid': organization.is_access_code_valid() if organization.access_code else False,
        'superadmin_org_id': organization.id if user.is_superadmin() else None,
    }
    
    return render(request, 'accounts/admin/access_code.html', context)


@login_required
@role_required(['admin', 'superadmin'])
@require_http_methods(['POST'])
def regenerate_access_code_view(request):
    """
    Regenerate access code for admin's organization.
    Invalidates old code and generates new one.
    """
    user = request.user
    
    if user.is_superadmin():
        org_id = (request.POST.get('organization_id') or '').strip()
        if not org_id:
            messages.error(request, 'Missing organization. Choose an organization first.')
            return redirect('accounts:admin_access_code')
        try:
            organization = SchoolGroup.objects.get(pk=int(org_id))
        except (ValueError, SchoolGroup.DoesNotExist):
            messages.error(request, 'Organization not found.')
            return redirect('accounts:superadmin_schoolgroups')
    else:
        organization = get_user_school_group(user)
        if not organization:
            messages.error(request, 'You must be a member of an organization to regenerate access codes.')
            return redirect('accounts:dashboard')
    
    try:
        old_code_formatted = organization.get_formatted_access_code() if organization.access_code else None
        new_code = organization.regenerate_access_code()
        new_code_formatted = organization.get_formatted_access_code()
        messages.success(
            request,
            f'Access code regenerated successfully. Old code "{old_code_formatted}" is now invalid. '
            f'New code: "{new_code_formatted}"'
        )
    except Exception:
        logger.exception('regenerate_access_code failed')
        messages.error(request, 'Failed to regenerate access code. Please try again.')
    
    if user.is_superadmin():
        return redirect(
            f"{reverse('accounts:admin_access_code')}?organization_id={organization.id}"
        )

    return redirect('accounts:admin_access_code')


# Superadmin School Groups Management

@login_required
@superadmin_required
def superadmin_schoolgroups_list_view(request):
    """List all school groups with filtering and search."""
    school_groups = SchoolGroup.objects.annotate(
        member_count=Count('memberships', filter=Q(memberships__status='accepted')),
        admin_count=Count('memberships', filter=Q(memberships__status='accepted', memberships__user__role__in=['admin', 'superadmin']))
    ).order_by('-created_at')
    
    # Search filter
    search_query = request.GET.get('q')
    if search_query:
        school_groups = school_groups.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        school_groups = school_groups.filter(is_active=True)
    elif status_filter == 'inactive':
        school_groups = school_groups.filter(is_active=False)
    
    # Plan filter
    plan_filter = request.GET.get('plan')
    if plan_filter and plan_filter in ['free', 'pro', 'enterprise']:
        school_groups = school_groups.filter(plan=plan_filter)
    
    context = {
        'school_groups': school_groups,
        'search_query': search_query,
        'status_filter': status_filter,
        'plan_filter': plan_filter,
        'total_count': SchoolGroup.objects.count(),
        'active_count': SchoolGroup.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'accounts/superadmin/schoolgroups_list.html', context)


@login_required
@superadmin_required
def superadmin_schoolgroup_detail_view(request, schoolgroup_id):
    """View details of a school group."""
    school_group = get_object_or_404(
        SchoolGroup.objects.select_related('created_by'),
        id=schoolgroup_id
    )
    
    # Get members
    members = User.objects.filter(
        memberships__school_group=school_group,
        memberships__status='accepted'
    ).select_related().distinct()
    
    # Get pending join requests
    pending_requests = JoinRequest.objects.filter(
        school_group=school_group,
        status='pending'
    ).select_related('user').order_by('-created_at')
    
    # Get statistics
    from chats.models import Chat
    from tickets.models import Ticket
    from knowledge.models import Article
    
    stats = {
        'total_members': members.count(),
        'admin_count': members.filter(role__in=['admin', 'superadmin']).count(),
        'total_chats': Chat.objects.filter(school_group=school_group).count(),
        'active_chats': Chat.objects.filter(school_group=school_group, status='active').count(),
        'total_tickets': Ticket.objects.filter(school_group=school_group).count(),
        'open_tickets': Ticket.objects.filter(school_group=school_group, status__in=['open', 'in_progress']).count(),
        'total_articles': Article.objects.filter(school_group=school_group).count(),
        'published_articles': Article.objects.filter(school_group=school_group, status='published').count(),
    }
    
    context = {
        'school_group': school_group,
        'members': members,
        'pending_requests': pending_requests,
        'stats': stats,
    }
    
    return render(request, 'accounts/superadmin/schoolgroup_detail.html', context)


@login_required
@superadmin_required
@require_http_methods(['GET', 'POST'])
def superadmin_schoolgroup_edit_view(request, schoolgroup_id):
    """Edit school group settings."""
    school_group = get_object_or_404(SchoolGroup, id=schoolgroup_id)
    
    if request.method == 'POST':
        # Update fields
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        plan = request.POST.get('plan', 'free')
        admin_limit = request.POST.get('admin_limit', '1')
        ai_enabled = request.POST.get('ai_enabled') == 'on'
        ai_plan = request.POST.get('ai_plan', 'limited')
        
        # Validate
        if not name:
            messages.error(request, 'Name is required.')
            return redirect('accounts:superadmin_schoolgroup_edit', schoolgroup_id=schoolgroup_id)
        
        # Check for duplicate name
        if name != school_group.name and SchoolGroup.objects.filter(name=name).exists():
            messages.error(request, 'A school group with this name already exists.')
            return redirect('accounts:superadmin_schoolgroup_edit', schoolgroup_id=schoolgroup_id)
        
        # Update
        old_plan = school_group.plan
        school_group.name = name
        school_group.description = description
        school_group.is_active = is_active
        school_group.plan = plan
        school_group.admin_limit = int(admin_limit) if admin_limit.isdigit() else 1
        school_group.ai_enabled = ai_enabled
        school_group.ai_plan = ai_plan
        school_group.save()
        
        # Log audit action
        log_action(
            request.user,
            'settings_changed',
            school_group,
            f'School group "{school_group.name}" settings updated.',
            school_group
        )
        
        if old_plan != plan:
            log_action(
                request.user,
                'settings_changed',
                school_group,
                f'School group "{school_group.name}" plan changed from {old_plan} to {plan}.',
                school_group
            )
        
        messages.success(request, f'School group "{school_group.name}" updated successfully.')
        return redirect('accounts:superadmin_schoolgroup_detail', schoolgroup_id=schoolgroup_id)
    
    from schoolgroups.models import PLAN_CHOICES, AI_PLAN_CHOICES
    
    context = {
        'school_group': school_group,
        'plan_choices': PLAN_CHOICES,
        'ai_plan_choices': AI_PLAN_CHOICES,
    }
    
    return render(request, 'accounts/superadmin/schoolgroup_edit.html', context)


@login_required
@superadmin_required
def superadmin_schoolgroup_members_view(request, schoolgroup_id):
    """View and manage members of a school group."""
    school_group = get_object_or_404(SchoolGroup, id=schoolgroup_id)
    
    # Get all memberships
    memberships = SchoolGroupMembership.objects.filter(
        school_group=school_group
    ).select_related('user').order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter and status_filter in ['pending', 'accepted', 'denied']:
        memberships = memberships.filter(status=status_filter)
    
    # Search filter
    search_query = request.GET.get('q')
    if search_query:
        memberships = memberships.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    context = {
        'school_group': school_group,
        'memberships': memberships,
        'status_filter': status_filter,
        'search_query': search_query,
        'accepted_count': memberships.filter(status='accepted').count(),
        'pending_count': memberships.filter(status='pending').count(),
    }
    
    return render(request, 'accounts/superadmin/schoolgroup_members.html', context)


# Superadmin Roles Management

@login_required
@superadmin_required
def superadmin_roles_list_view(request):
    """List all users with role filtering and search."""
    users = User.objects.all().order_by('-date_joined')
    
    # Search filter
    search_query = request.GET.get('q')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    # Role filter
    role_filter = request.GET.get('role')
    if role_filter and role_filter in ['user', 'admin', 'superadmin']:
        users = users.filter(role=role_filter)
    
    # Get user organizations count
    users = users.annotate(
        organization_count=Count('memberships', filter=Q(memberships__status='accepted'))
    )
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'total_count': User.objects.count(),
        'user_count': User.objects.filter(role='user').count(),
        'admin_count': User.objects.filter(role='admin').count(),
        'superadmin_count': User.objects.filter(role='superadmin').count(),
    }
    
    return render(request, 'accounts/superadmin/roles_list.html', context)


@login_required
@superadmin_required
@require_http_methods(['GET', 'POST'])
def superadmin_role_assign_view(request, user_id):
    """Assign or change a user's role."""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        new_role = request.POST.get('role', '').strip()
        
        if new_role not in ['user', 'admin', 'superadmin']:
            messages.error(request, 'Invalid role selected.')
            return redirect('accounts:superadmin_role_assign', user_id=user_id)
        
        old_role = user.role
        if old_role == new_role:
            messages.info(request, f'User {user.email} already has the role {new_role}.')
            return redirect('accounts:superadmin_roles')
        
        # Prevent removing the last superadmin
        if old_role == 'superadmin' and new_role != 'superadmin':
            superadmin_count = User.objects.filter(role='superadmin').count()
            if superadmin_count <= 1:
                messages.error(request, 'Cannot remove the last superadmin. Please assign another superadmin first.')
                return redirect('accounts:superadmin_role_assign', user_id=user_id)
        
        # Update role
        user.role = new_role
        user.save(update_fields=['role'])
        
        # Log audit action
        log_action(
            request.user,
            'role_changed',
            user,
            f'User {user.email} role changed from {old_role} to {new_role}.',
            None
        )
        
        messages.success(request, f'Role updated successfully. {user.email} is now a {new_role}.')
        return redirect('accounts:superadmin_roles')
    
    context = {
        'target_user': user,
        'role_choices': User.ROLE_CHOICES,
    }
    
    return render(request, 'accounts/superadmin/role_assign.html', context)


@login_required
@superadmin_required
@require_http_methods(['POST'])
def superadmin_role_bulk_assign_view(request):
    """Bulk assign roles to multiple users."""
    user_ids = request.POST.getlist('user_ids')
    new_role = request.POST.get('role', '').strip()
    
    if not user_ids:
        messages.error(request, 'No users selected.')
        return redirect('accounts:superadmin_roles')
    
    if new_role not in ['user', 'admin', 'superadmin']:
        messages.error(request, 'Invalid role selected.')
        return redirect('accounts:superadmin_roles')
    
    users = User.objects.filter(id__in=user_ids)
    updated_count = 0
    
    for user in users:
        if user.role != new_role:
            # Prevent removing the last superadmin
            if user.role == 'superadmin' and new_role != 'superadmin':
                superadmin_count = User.objects.filter(role='superadmin').count()
                if superadmin_count <= 1:
                    continue  # Skip this user
            
            old_role = user.role
            user.role = new_role
            user.save(update_fields=['role'])
            
            # Log audit action
            log_action(
                request.user,
                'role_changed',
                user,
                f'User {user.email} role changed from {old_role} to {new_role} (bulk update).',
                None
            )
            
            updated_count += 1
    
    if updated_count > 0:
        messages.success(request, f'Successfully updated {updated_count} user(s) to {new_role}.')
    else:
        messages.info(request, 'No users were updated.')
    
    return redirect('accounts:superadmin_roles')


# Superadmin System Settings

@login_required
@superadmin_required
@require_http_methods(['GET', 'POST'])
def superadmin_settings_view(request):
    """System settings management page."""
    from django.conf import settings
    
    if request.method == 'POST':
        # For now, this is a placeholder - settings would typically be stored in database
        # or environment variables. This view shows current settings and allows viewing.
        messages.info(request, 'Settings management is currently read-only. Configuration changes require environment variable updates.')
        return redirect('accounts:superadmin_settings')
    
    # Get current settings (read-only display)
    current_settings = {
        'debug': getattr(settings, 'DEBUG', False),
        'allowed_hosts': ', '.join(getattr(settings, 'ALLOWED_HOSTS', [])),
        'email_backend': getattr(settings, 'EMAIL_BACKEND', 'Not configured'),
        'google_oauth_enabled': bool(getattr(settings, 'GOOGLE_OAUTH2_CLIENT_ID', None)),
        'gemini_ai_enabled': bool(getattr(settings, 'GOOGLE_GEMINI_API_KEY', None)),
        'gemini_model': getattr(settings, 'GEMINI_MODEL', 'Not set'),
    }
    
    context = {
        'settings': current_settings,
    }
    
    return render(request, 'accounts/superadmin/settings.html', context)

