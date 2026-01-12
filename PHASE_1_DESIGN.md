# Phase 1: Foundation - Design Plan

## Overview
Set up the core foundation: Django project structure, authentication system, role-based access control, and base dark mode templates.

## What We'll Build

### 1. Django Project Structure
- Initialize Django project: `helpme_hub`
- Create Django apps:
  - `accounts` - Authentication and user management
  - `schoolgroups` - School group management (basic structure)
- Set up project directory structure
- Configure `settings.py` with all necessary settings

### 2. Database Configuration
- PostgreSQL configuration using `dj-database-url`
- Database settings for local (SQLite option) and production (PostgreSQL)
- Migration setup

### 3. Authentication System
- Custom User model extending Django's AbstractUser
- User fields: username, email, first_name, last_name, role, dark_mode_preference
- Role choices: 'user', 'admin', 'superadmin'
- Django Allauth integration for:
  - Traditional email/password registration
  - Google OAuth authentication
- Login, Register, Logout views
- Authentication templates

### 4. Role-Based Access Control
- Custom decorators:
  - `@role_required(roles=['admin', 'superadmin'])`
  - `@superadmin_required`
- Middleware for role checking (optional, can use decorators)
- Permission utilities

### 5. Base Templates (Dark Mode)
- `base.html` - Main base template with:
  - Dark mode styling (Tailwind CSS)
  - Navigation bar
  - Sidebar (responsive)
  - Footer
  - Dark mode toggle functionality
- `loading.html` - Loading page
- Template structure for all pages

### 6. Navigation Shells
- Desktop navigation: Full nav bar with sidebar
- Mobile navigation: Hamburger menu
- Role-based menu items
- Dark mode toggle
- User profile dropdown

### 7. Core Pages (Minimal)
- Loading page (`/loading/`)
- Login page (`/accounts/login/`)
- Register page (`/accounts/register/`)
- Dashboard placeholder (`/dashboard/`) - Role-based redirect
- Profile page (`/profile/`)

### 8. Configuration Files
- `.env.example` - Environment variables template
- `runtime.txt` - Python version for Railway
- Update `requirements.txt` with actual installed versions
- Railway deployment configuration notes

## File Structure to Create

```
helpme_hub/
├── manage.py
├── requirements.txt
├── .env.example
├── runtime.txt
├── .gitignore (already exists)
├── helpme_hub/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/
│   ├── __init__.py
│   ├── models.py (User model)
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── decorators.py (role checking)
│   └── admin.py
├── schoolgroups/
│   ├── __init__.py
│   ├── models.py (basic structure)
│   └── admin.py
├── static/
│   ├── css/
│   │   └── custom.css
│   └── js/
│       ├── darkmode.js
│       └── navigation.js
└── templates/
    ├── base.html
    ├── loading.html
    ├── accounts/
    │   ├── login.html
    │   ├── register.html
    │   └── profile.html
    └── dashboard.html
```

## Key Implementation Details

### User Model
```python
class User(AbstractUser):
    role = CharField(choices=[('user', 'User'), ('admin', 'Admin'), ('superadmin', 'Superadmin')])
    dark_mode_preference = BooleanField(default=True)
    # ... other fields
```

### Settings Configuration
- Database: PostgreSQL with SQLite fallback for local dev
- Static files: WhiteNoise configuration
- Authentication: Django Allauth setup
- Security: CSRF, XSS protection
- Environment variables: python-decouple

### Dark Mode Implementation
- Tailwind CSS via CDN
- Color palette: gray-900 background, gray-800 cards, blue-600 accents
- JavaScript for dark mode toggle (localStorage)
- CSS custom styles for dark mode

### Responsive Navigation
- Desktop: Sidebar always visible
- Tablet: Collapsible sidebar
- Mobile: Hamburger menu with slide-in drawer

## Testing Checklist (After Phase 1)

1. ✅ Django project runs without errors
2. ✅ Database migrations run successfully
3. ✅ Can create superuser
4. ✅ Login page works (traditional)
5. ✅ Registration page works
6. ✅ Google OAuth button appears (even if not fully configured)
7. ✅ Role-based access works (test with different roles)
8. ✅ Dark mode toggle works
9. ✅ Navigation responsive on mobile/tablet/desktop
10. ✅ Loading page displays correctly

## What We're NOT Building Yet

- ❌ School group functionality (Phase 2)
- ❌ Chat system (Phase 3)
- ❌ Tickets (Phase 4)
- ❌ Knowledge base (Phase 5)
- ❌ Full dashboard content (just placeholder)

## Next Steps After Phase 1

Once Phase 1 is complete:
1. Summary of what was built
2. Manual test steps
3. Preview of Phase 2

---

**Ready to implement Phase 1: Foundation**


