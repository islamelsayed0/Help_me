from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache
from django.db import models
from django.conf import settings
import logging
from .decorators import role_required, membership_required
from .forms import UserRegistrationForm, JoinRequestForm, CreateOrganizationForm
from schoolgroups.models import SchoolGroup, JoinRequest, SchoolGroupMembership
from .utils import has_accepted_membership, get_user_pending_join_request, get_user_school_group, get_user_organizations
from .models import User
from django.utils import timezone

logger = logging.getLogger(__name__)


def home_view(request):
    """
    Root URL view - shows landing page or redirects to dashboard.
    If logged in, check membership and redirect accordingly.
    If not logged in, show landing page.
    """
    if request.user.is_authenticated:
        # Check if user has accepted membership
        if has_accepted_membership(request.user):
            return redirect('accounts:dashboard')
        else:
            # Redirect to pending page if no accepted membership
            return redirect('accounts:pending')
    else:
        return render(request, 'landing.html')


def loading_view(request):
    """Loading page shown during initial app load."""
    return render(request, 'loading.html')


@never_cache
@csrf_protect
@require_http_methods(['GET', 'POST'])
def login_view(request):
    """Custom login view that properly handles authentication errors."""
    if request.user.is_authenticated:
        # Redirect authenticated users appropriately
        if has_accepted_membership(request.user):
            return redirect('accounts:dashboard')
        else:
            return redirect('accounts:pending')
    
    if request.method == 'POST':
        email = request.POST.get('login', '').strip().lower()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember') == 'on'
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
        else:
            # Try to get user by email (for email-based authentication)
            try:
                user_obj = User.objects.get(email=email)
                
                # With ACCOUNT_AUTHENTICATION_METHOD = 'email', Allauth expects email as username
                # Try authentication with email first (for Allauth backend)
                # Then try with username (for ModelBackend fallback)
                user = authenticate(request, username=email, password=password)
                if user is None:
                    # Fallback to username (for ModelBackend)
                    user = authenticate(request, username=user_obj.username, password=password)
                
                if user is not None and user.is_active:
                    # User authenticated successfully
                    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                    
                    if not remember:
                        request.session.set_expiry(0)  # Session expires when browser closes
                    else:
                        request.session.set_expiry(86400 * 30)  # 30 days
                    
                    # Redirect based on membership status
                    if has_accepted_membership(user):
                        messages.success(request, f'Welcome back, {user.email}!')
                        return redirect('accounts:dashboard')
                    else:
                        messages.success(request, f'Welcome, {user.email}! Please complete your organization membership.')
                        return redirect('accounts:pending')
                else:
                    # Authentication failed - wrong password or inactive account
                    # Check password manually to provide better error message
                    if not user_obj.is_active:
                        messages.error(request, 'This account is inactive. Please contact support.')
                    elif not user_obj.check_password(password):
                        # Password is incorrect
                        messages.error(request, 'Wrong account information. Please check your email and password and try again.')
                    else:
                        # Password is correct but authentication still failed - unexpected
                        messages.error(request, 'An authentication error occurred. Please try again or contact support.')
            except User.DoesNotExist:
                # User doesn't exist
                messages.error(request, 'Wrong account information. Please check your email and password and try again.')
            except Exception as e:
                # Unexpected error
                logger.error(f'Login error: {str(e)}', exc_info=True)
                messages.error(request, 'An error occurred during login. Please try again.')
    
    return render(request, 'accounts/login.html')


@require_http_methods(['GET', 'POST'])
def register_view(request):
    """User registration view."""
    import logging
    logger = logging.getLogger(__name__)

    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            try:
                # Save user to database
                user = form.save()
                logger.info(f'User created successfully: {user.email} (ID: {user.id})')

                # Verify user was saved
                if not user.pk:
                    logger.error(f'User save failed - no primary key: {user.email}')
                    messages.error(request, 'Account creation failed. Please try again.')
                    return render(request, 'accounts/register.html', {'form': form})
                
                # Log in the user
                try:
                    # Since UserCreationForm.save() already hashes the password,
                    # we can log in directly with the user object.
                    
                    # Ensure user has valid id before logging in
                    if not user.id:
                        logger.error(f'Cannot login user without ID: {user.email}')
                        messages.error(request, 'Account creation failed. Please try again.')
                        return render(request, 'accounts/register.html', {'form': form})
                    
                    # Use ModelBackend which is the first backend in AUTHENTICATION_BACKENDS
                    backend = 'django.contrib.auth.backends.ModelBackend'
                    
                    # Log in the user - this sets request.user and persists it in the session
                    # Django's login() function:
                    # 1. Sets request.user to the authenticated user
                    # 2. Stores auth data in session (_auth_user_id, _auth_user_backend)
                    # 3. Marks session as modified
                    # SessionMiddleware will save the session when the response is sent
                    login(request, user, backend=backend)
                    logger.info(f'Login called for user: {user.email} (ID: {user.id}, username: {user.username}, session_key: {request.session.session_key})')

                    # CRITICAL: Verify login worked immediately
                    # After login(), request.user should be the authenticated user
                    # Django's login() sets request.user immediately, so check right after
                    if not request.user.is_authenticated or request.user.id != user.id:
                        logger.error(f'Login() failed - user not authenticated or ID mismatch after login() call: {user.email}, authenticated={request.user.is_authenticated}, user_id={getattr(request.user, "id", None)}, expected_id={user.id}')
                        messages.error(request, 'Account created successfully, but automatic login failed. Please log in manually with your credentials.')
                        return redirect('accounts:login')
                    
                    # Login successful - session is automatically saved by SessionMiddleware
                    logger.info(f'User successfully logged in: {user.email} (ID: {user.id})')
                    messages.success(request, 'Registration successful! Welcome to HelpMe Hub.')

                    # Redirect to pending page since new users don't have membership yet
                    # SessionMiddleware will save the session when the redirect response is sent
                    return redirect('accounts:pending')
                        
                except Exception as e:
                    logger.error(f'Login exception for user {user.email}: {str(e)}', exc_info=True)
                    import traceback
                    logger.error(f'Traceback: {traceback.format_exc()}')
                    # User account was created, so inform them to log in manually
                    messages.error(request, f'Account created successfully, but an error occurred during login: {str(e)}. Please log in manually.')
                    return redirect('accounts:login')
                    
            except Exception as e:
                logger.error(f'Registration error: {str(e)}', exc_info=True)
                messages.error(request, f'An error occurred during registration: {str(e)}. Please try again.')
                # Re-render form with errors
                return render(request, 'accounts/register.html', {'form': form})
        else:
            # Form validation failed - display errors on registration page
            logger.warning(f'Registration form validation failed: {form.errors}')
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


@login_required
@require_http_methods(['GET', 'POST'])
def pending_view(request):
    """
    Pending approval page.
    Shows join request status and form to request join.
    Now accessible to users with existing memberships who want to join additional organizations.
    """

    user = request.user


    # Get user's pending join requests (all of them)
    pending_requests = JoinRequest.objects.filter(user=user, status='pending').select_related('school_group')
    
    # Get all memberships to show status
    memberships = SchoolGroupMembership.objects.filter(user=user).select_related('school_group').order_by('-created_at')
    
    # Check if user can create an organization
    can_create_organization = not user.has_created_organization()
    
    # Show form if user doesn't have accepted membership, or always show for joining additional orgs
    show_join_form = True
    
    context = {
        'user': user,
        'pending_requests': pending_requests,
        'pending_request': pending_requests.first(),  # For backward compatibility
        'memberships': memberships,
        'form': JoinRequestForm(user=user) if show_join_form else None,
        'can_create_organization': can_create_organization,
        'has_accepted_membership': has_accepted_membership(user),
    }

    return render(request, 'accounts/pending.html', context)


@login_required
@require_http_methods(['POST'])
def request_join_view(request):
    """
    Handle join request creation using access code.
    Creates JoinRequest and SchoolGroupMembership (status='pending').
    Allows users with existing memberships to join additional organizations.
    """
    user = request.user
    
    form = JoinRequestForm(request.POST, user=user)
    
    if form.is_valid():
        # Get school_group from form's cleaned_data (set during validation)
        school_group = form.cleaned_data.get('school_group')
        
        if not school_group:
            messages.error(request, 'Invalid access code.')
            # Redirect to referring page or appropriate default
            next_url = request.GET.get('next') or request.META.get('HTTP_REFERER')
            if next_url and next_url.startswith(request.build_absolute_uri('/')):
                return redirect(next_url)
            elif has_accepted_membership(user):
                return redirect('accounts:dashboard')
            else:
                return redirect('accounts:pending')
        
        # Check if request already exists (double-check)
        if JoinRequest.objects.filter(
            user=user,
            school_group=school_group,
            status='pending'
        ).exists():
            messages.warning(request, 'You already have a pending request for this organization.')
            next_url = request.GET.get('next') or request.META.get('HTTP_REFERER')
            if next_url and next_url.startswith(request.build_absolute_uri('/')):
                return redirect(next_url)
            elif has_accepted_membership(user):
                return redirect('accounts:dashboard')
            else:
                return redirect('accounts:pending')
        
        # Check if membership already exists
        if SchoolGroupMembership.objects.filter(
            user=user,
            school_group=school_group
        ).exists():
            messages.warning(request, 'You already have a membership for this organization.')
            next_url = request.GET.get('next') or request.META.get('HTTP_REFERER')
            if next_url and next_url.startswith(request.build_absolute_uri('/')):
                return redirect(next_url)
            elif has_accepted_membership(user):
                return redirect('accounts:dashboard')
            else:
                return redirect('accounts:pending')
        
        # Create join request
        join_request = JoinRequest.objects.create(
            user=user,
            school_group=school_group,
            status='pending'
        )
        
        # Log audit action
        from audit.utils import log_join_request_created
        log_join_request_created(user, join_request)
        
        # Create membership with pending status
        SchoolGroupMembership.objects.create(
            user=user,
            school_group=school_group,
            status='pending'
        )
        
        messages.success(
            request,
            f'Your request to join {school_group.name} has been submitted. '
            'An administrator will review your request shortly.'
        )
        
        # Smart redirect based on context
        next_url = request.GET.get('next') or request.META.get('HTTP_REFERER')
        if next_url and next_url.startswith(request.build_absolute_uri('/')):
            return redirect(next_url)
        elif has_accepted_membership(user):
            return redirect('accounts:dashboard')
        else:
            return redirect('accounts:pending')
    else:
        # Form errors will be displayed in template
        messages.error(request, 'Please correct the errors below.')
        next_url = request.GET.get('next') or request.META.get('HTTP_REFERER')
        if next_url and next_url.startswith(request.build_absolute_uri('/')):
            return redirect(next_url)
        elif has_accepted_membership(user):
            return redirect('accounts:dashboard')
        else:
            return redirect('accounts:pending')


@login_required
@require_http_methods(['GET', 'POST'])
def create_organization_view(request):
    """
    Handle organization creation.
    Creates SchoolGroup and makes user admin with accepted membership.
    """
    user = request.user
    
    # Check if user has already created an organization
    if user.has_created_organization():
        messages.warning(request, 'You have already created an organization. Each user can only create one organization.')
        return redirect('accounts:pending')
    
    if request.method == 'POST':
        form = CreateOrganizationForm(request.POST, user=user)
        if form.is_valid():
            name = form.cleaned_data['name']
            description = form.cleaned_data.get('description', '')
            
            # Create the organization
            organization = SchoolGroup.objects.create(
                name=name,
                description=description,
                created_by=user,
                is_active=True,
                plan='free',
                admin_limit=10,
                ai_enabled=True,
                ai_plan='limited'
            )
            
            # Generate access code for the new organization
            try:
                organization.generate_access_code()
            except Exception as e:
                # Log error but don't fail organization creation
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f'Failed to generate access code for organization {organization.id}: {e}')
            
            # Create membership with accepted status
            membership = SchoolGroupMembership.objects.create(
                user=user,
                school_group=organization,
                status='accepted',
                joined_at=timezone.now()
            )
            
            # Set user role to admin if currently user
            if user.role == 'user':
                user.role = 'admin'
                user.save()
            
            # Set current organization
            user.current_organization = organization
            user.save()
            
            messages.success(
                request,
                f'Organization "{organization.name}" has been created successfully! '
                'You are now the administrator of this organization.'
            )
            return redirect('accounts:dashboard')
    else:
        form = CreateOrganizationForm(user=user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'accounts/create_organization.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def join_organization_view(request):
    """
    Dedicated page for joining an organization using an access code.
    Works for users with or without existing memberships.
    """
    user = request.user
    
    if request.method == 'POST':
        form = JoinRequestForm(request.POST, user=user)
        if form.is_valid():
            # Form validation and join request creation handled in request_join_view
            # This view just renders the form, actual submission goes to request_join_view
            pass
    else:
        form = JoinRequestForm(user=user)
    
    # Get user's current organizations and pending requests
    user_organizations = get_user_organizations(user)
    pending_requests = JoinRequest.objects.filter(user=user, status='pending').select_related('school_group')
    memberships = SchoolGroupMembership.objects.filter(user=user).select_related('school_group').order_by('-created_at')
    
    context = {
        'form': form,
        'user_organizations': user_organizations,
        'pending_requests': pending_requests,
        'memberships': memberships,
        'has_accepted_membership': has_accepted_membership(user),
    }
    
    return render(request, 'accounts/join_organization.html', context)


@login_required
@require_http_methods(['POST'])
def switch_organization_view(request):
    """
    Handle organization switching.
    Updates user's current_organization field.
    """
    user = request.user
    
    organization_id = request.POST.get('organization_id')
    if not organization_id:
        messages.error(request, 'Please select an organization.')
        return redirect('accounts:profile')
    
    try:
        organization = SchoolGroup.objects.get(id=organization_id)
    except SchoolGroup.DoesNotExist:
        messages.error(request, 'Organization not found.')
        return redirect('accounts:profile')
    
    # Verify user is a member of this organization
    membership = SchoolGroupMembership.objects.filter(
        user=user,
        school_group=organization,
        status='accepted'
    ).first()
    
    if not membership:
        messages.error(request, 'You are not a member of this organization.')
        return redirect('accounts:profile')
    
    # Update current organization
    user.current_organization = organization
    user.save(update_fields=['current_organization'])
    
    messages.success(request, f'Switched to {organization.name}.')
    return redirect('accounts:dashboard')


@login_required
def dashboard_view(request):
    """Dashboard view - redirects based on user role."""
    user = request.user
    
    # Check if user has accepted membership, if not redirect to pending
    if not has_accepted_membership(user):
        return redirect('accounts:pending')
    
    # Get user's organizations and pending requests for context
    user_organizations = get_user_organizations(user)
    pending_requests = JoinRequest.objects.filter(user=user, status='pending').select_related('school_group')
    user_org = get_user_school_group(user)
    
    # Import models for statistics
    from chats.models import Chat
    from tickets.models import Ticket
    
    # Calculate user statistics (filtered by current organization)
    stats = {
        'total_chats': Chat.objects.filter(user=user, school_group=user_org).count(),
        'active_chats': Chat.objects.filter(user=user, school_group=user_org, status='active').count(),
        'resolved_chats': Chat.objects.filter(user=user, school_group=user_org, status='resolved').count(),
        'total_tickets': Ticket.objects.filter(user=user, school_group=user_org).count(),
        'open_tickets': Ticket.objects.filter(user=user, school_group=user_org, status='open').count(),
        'in_progress_tickets': Ticket.objects.filter(user=user, school_group=user_org, status='in_progress').count(),
        'resolved_tickets': Ticket.objects.filter(user=user, school_group=user_org, status='resolved').count(),
    }
    
    # Get recent activity (last 5 chats and tickets)
    recent_chats = Chat.objects.filter(user=user, school_group=user_org).select_related('assigned_to').order_by('-updated_at')[:5]
    recent_tickets = Ticket.objects.filter(user=user, school_group=user_org).select_related('assigned_to').order_by('-updated_at')[:5]
    
    context = {
        'user': user,
        'user_organizations': user_organizations,
        'pending_requests': pending_requests,
        'join_form': JoinRequestForm(user=user),
        'stats': stats,
        'recent_chats': recent_chats,
        'recent_tickets': recent_tickets,
        'user_org': user_org,
    }
    
    if user.is_superadmin():
        return redirect('accounts:superadmin_dashboard')
    elif user.is_admin():
        return redirect('accounts:admin_dashboard')
    else:
        return render(request, 'dashboard.html', context)


@login_required
@role_required(['admin', 'superadmin'])
def admin_dashboard_view(request):
    """Admin dashboard view with org-level stats and recent activity."""
    user = request.user
    user_organizations = get_user_organizations(user)
    pending_requests = JoinRequest.objects.filter(user=user, status='pending').select_related('school_group')
    user_org = get_user_school_group(user)
    
    from chats.models import Chat
    from tickets.models import Ticket
    from inventory.models import InventoryItem
    
    # Org-level stats (admin sees their organization's activity)
    if user_org:
        stats = {
            'total_chats': Chat.objects.filter(school_group=user_org).count(),
            'active_chats': Chat.objects.filter(school_group=user_org, status='active').count(),
            'resolved_chats': Chat.objects.filter(school_group=user_org, status='resolved').count(),
            'total_tickets': Ticket.objects.filter(school_group=user_org).count(),
            'open_tickets': Ticket.objects.filter(school_group=user_org, status='open').count(),
            'in_progress_tickets': Ticket.objects.filter(school_group=user_org, status='in_progress').count(),
            'resolved_tickets': Ticket.objects.filter(school_group=user_org, status='resolved').count(),
        }

        # Simple analytics cards
        # 1) Open tickets (open + in_progress)
        open_tickets_count = Ticket.objects.filter(
            school_group=user_org,
            status__in=['open', 'in_progress'],
        ).count()

        # 2) Low-stock inventory items
        from django.db.models import F
        low_stock_count = InventoryItem.objects.filter(
            school_group=user_org,
            min_stock__gt=0,
            quantity__lte=F('min_stock'),
        ).count()

        # 3) Active users in last 7 days (based on ticket creation)
        from django.utils import timezone
        from datetime import timedelta
        since = timezone.now() - timedelta(days=7)
        active_users_last_7_days = Ticket.objects.filter(
            school_group=user_org,
            created_at__gte=since,
        ).values('user').distinct().count()

        recent_chats = Chat.objects.filter(school_group=user_org).select_related('assigned_to').order_by('-updated_at')[:5]
        recent_tickets = Ticket.objects.filter(school_group=user_org).select_related('assigned_to').order_by('-updated_at')[:5]
    else:
        stats = {
            'total_chats': 0, 'active_chats': 0, 'resolved_chats': 0,
            'total_tickets': 0, 'open_tickets': 0, 'in_progress_tickets': 0, 'resolved_tickets': 0,
        }
        open_tickets_count = 0
        low_stock_count = 0
        active_users_last_7_days = 0
        recent_chats = []
        recent_tickets = []
    
    context = {
        'user': user,
        'user_organizations': user_organizations,
        'pending_requests': pending_requests,
        'join_form': JoinRequestForm(user=user),
        'stats': stats,
        'recent_chats': recent_chats,
        'recent_tickets': recent_tickets,
        'user_org': user_org,
        'open_tickets_count': open_tickets_count,
        'low_stock_count': low_stock_count,
        'active_users_last_7_days': active_users_last_7_days,
    }
    return render(request, 'dashboard.html', context)


@login_required
@role_required(['superadmin'])
def superadmin_dashboard_view(request):
    """Superadmin dashboard view with system-wide statistics."""
    from chats.models import Chat
    from tickets.models import Ticket
    from knowledge.models import Article
    from audit.models import AuditLog
    
    user = request.user
    
    # System-wide statistics
    stats = {
        'total_users': User.objects.count(),
        'total_admins': User.objects.filter(role__in=['admin', 'superadmin']).count(),
        'total_superadmins': User.objects.filter(role='superadmin').count(),
        'total_school_groups': SchoolGroup.objects.count(),
        'active_school_groups': SchoolGroup.objects.filter(is_active=True).count(),
        'total_chats': Chat.objects.count(),
        'active_chats': Chat.objects.filter(status='active').count(),
        'total_tickets': Ticket.objects.count(),
        'open_tickets': Ticket.objects.filter(status__in=['open', 'in_progress']).count(),
        'total_articles': Article.objects.count(),
        'published_articles': Article.objects.filter(status='published').count(),
        'total_audit_logs': AuditLog.objects.count(),
        'pending_join_requests': JoinRequest.objects.filter(status='pending').count(),
    }
    
    # Recent activity (last 10 audit logs)
    recent_activity = AuditLog.objects.select_related('actor', 'school_group').order_by('-created_at')[:10]
    
    # School groups with member counts
    school_groups = SchoolGroup.objects.annotate(
        member_count=models.Count('memberships', filter=models.Q(memberships__status='accepted'))
    ).order_by('-created_at')[:10]
    
    context = {
        'user': user,
        'stats': stats,
        'recent_activity': recent_activity,
        'school_groups': school_groups,
    }
    return render(request, 'accounts/superadmin/dashboard.html', context)


@login_required
def profile_view(request):
    """User profile view."""
    user = request.user
    
    # Check if user has accepted membership, if not redirect to pending
    if not has_accepted_membership(user):
        return redirect('accounts:pending')
    school_group = get_user_school_group(user)
    memberships = SchoolGroupMembership.objects.filter(user=user).select_related('school_group')
    user_organizations = get_user_organizations(user)
    
    # Get pending requests
    pending_requests = JoinRequest.objects.filter(user=user, status='pending').select_related('school_group')
    
    context = {
        'user': user,
        'school_group': school_group,
        'memberships': memberships,
        'user_organizations': user_organizations,
        'pending_requests': pending_requests,
        'join_form': JoinRequestForm(user=user),
    }
    return render(request, 'accounts/profile.html', context)


@never_cache
@login_required
@membership_required
def subscription_view(request):
    """
    Support / Donate page. HelpMe Hub is free; donations help cover costs.
    """
    organization = get_user_school_group(request.user)
    if not organization:
        messages.error(request, 'You must be a member of an organization to view this page.')
        return redirect('accounts:pending')

    admin_count = organization.get_admin_count()
    donation_url = (getattr(settings, 'DONATION_URL', None) or '').strip()
    is_admin = request.user.is_admin()

    context = {
        'organization': organization,
        'admin_count': admin_count,
        'donation_url': donation_url if donation_url else None,
        'is_admin': is_admin,
    }
    return render(request, 'accounts/subscription.html', context)

