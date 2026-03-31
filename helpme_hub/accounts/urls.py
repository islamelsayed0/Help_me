from django.urls import path, re_path
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from allauth.account import views as allauth_account_views

from . import views
from . import admin_views

app_name = 'accounts'

_ratelimit_password_reset = method_decorator(
    ratelimit(key='ip', rate='5/h', method='POST', block=True),
    name='dispatch',
)(allauth_account_views.PasswordResetView)

_ratelimit_password_reset_key = method_decorator(
    ratelimit(key='ip', rate='20/h', method='POST', block=True),
    name='dispatch',
)(allauth_account_views.PasswordResetFromKeyView)

urlpatterns = [
    path(
        'password/reset/',
        _ratelimit_password_reset.as_view(),
        name='account_reset_password',
    ),
    re_path(
        r'^password/reset/key/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$',
        _ratelimit_password_reset_key.as_view(),
        name='account_reset_password_from_key',
    ),
    # Root URL - redirects to loading or dashboard
    path('', views.home_view, name='home'),
    
    # Loading page
    path('loading/', views.loading_view, name='loading'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard (role-based redirects)
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('superadmin/dashboard/', views.superadmin_dashboard_view, name='superadmin_dashboard'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    
    # Membership and Join Requests
    path('pending/', views.pending_view, name='pending'),
    path('join-organization/', views.join_organization_view, name='join_organization'),
    path('request-join/', views.request_join_view, name='request_join'),
    path('create-organization/', views.create_organization_view, name='create_organization'),
    path('switch-organization/', views.switch_organization_view, name='switch_organization'),
    
    # Admin Join Request Management
    path('admin/joinrequests/', admin_views.join_requests_list_view, name='admin_join_requests'),
    path('admin/joinrequests/<int:request_id>/', admin_views.join_request_detail_view, name='admin_join_request_detail'),
    path('admin/joinrequests/<int:request_id>/accept/', admin_views.accept_join_request_view, name='admin_accept_join_request'),
    path('admin/joinrequests/<int:request_id>/deny/', admin_views.deny_join_request_view, name='admin_deny_join_request'),
    
    # Admin Access Code Management
    path('admin/access-code/', admin_views.view_access_code_view, name='admin_access_code'),
    path('admin/access-code/regenerate/', admin_views.regenerate_access_code_view, name='admin_regenerate_access_code'),
    
    # Support / Donate (formerly Subscription)
    path('organization/subscription/', views.subscription_view, name='subscription'),
    path('organization/subscription/upgrade/', RedirectView.as_view(pattern_name='accounts:subscription', permanent=False)),
    path('organization/subscription/stripe/success/', RedirectView.as_view(pattern_name='accounts:subscription', permanent=False)),
    path('organization/subscription/stripe/cancel/', RedirectView.as_view(pattern_name='accounts:subscription', permanent=False)),

    # Legacy: AI Add-On page removed; redirect to Support
    path('ai-addon/', RedirectView.as_view(pattern_name='accounts:subscription', permanent=False)),

    # Superadmin School Groups Management
    path('superadmin/schoolgroups/', admin_views.superadmin_schoolgroups_list_view, name='superadmin_schoolgroups'),
    path('superadmin/schoolgroups/<int:schoolgroup_id>/', admin_views.superadmin_schoolgroup_detail_view, name='superadmin_schoolgroup_detail'),
    path('superadmin/schoolgroups/<int:schoolgroup_id>/edit/', admin_views.superadmin_schoolgroup_edit_view, name='superadmin_schoolgroup_edit'),
    path('superadmin/schoolgroups/<int:schoolgroup_id>/members/', admin_views.superadmin_schoolgroup_members_view, name='superadmin_schoolgroup_members'),
    
    # Superadmin Roles Management
    path('superadmin/roles/', admin_views.superadmin_roles_list_view, name='superadmin_roles'),
    path('superadmin/roles/<int:user_id>/assign/', admin_views.superadmin_role_assign_view, name='superadmin_role_assign'),
    path('superadmin/roles/bulk-assign/', admin_views.superadmin_role_bulk_assign_view, name='superadmin_role_bulk_assign'),
    
    # Superadmin System Settings
    path('superadmin/settings/', admin_views.superadmin_settings_view, name='superadmin_settings'),
]

