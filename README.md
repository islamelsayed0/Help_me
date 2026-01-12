# HelpMe Hub

A modern, calm, enterprise and school friendly IT support portal in dark mode.

## Overview

HelpMe Hub is a role based IT support portal that provides self service help, live admin chat, and ticket management. The application is designed with a calming dark mode interface suitable for both school and business environments.

## Features

### Core Functionality
- **School Group Based Access** - Data isolation by school groups
- **Role Based Access Control** - Three roles: User, Admin, Superadmin
- **Chat First Support** - Users start with chat, escalate to tickets when needed
- **Ticket Management** - Kanban board for admins to manage tickets
- **Knowledge Base** - Self service articles with markdown support, draft and published states
- **Join Request System** - Users request to join school groups, admins approve/deny
- **Audit Logs** - Track all important actions (approvals, role changes, ticket closures)
- **Superadmin Management** - Complete system administration tools (school groups, roles, settings)
- **Subscription Management** - Stripe integration for plan upgrades and AI Add-On billing
- **Email Notifications** - Automated emails for key events (registration, approvals, tickets)

### Authentication
- Traditional email/password registration
- Google OAuth (Gmail sign in)
- Secure session management

### User Experience
- **Dark Mode Only** - Calming, professional dark theme
- **Fully Responsive** - Mobile, tablet, and desktop friendly
- **Touch Optimized** - Mobile first design with touch friendly interactions
- **Consistent Design** - Same look and feel across all devices

## Tech Stack

### Backend
- **Django 4.2+** - Python web framework
- **PostgreSQL** - Database (via Railway)
- **Django Allauth** - Authentication with Google OAuth
- **Gunicorn** - WSGI server for production
- **WhiteNoise** - Static file serving
- **Stripe** - Payment processing and subscriptions
- **Markdown** - Knowledge base article rendering with syntax highlighting

### Frontend
- **Django Templates** - Server rendered HTML
- **Tailwind CSS** - Styling (via CDN)
- **Vanilla JavaScript** - Interactive features
- **No React** - Pure Django templates

### Hosting
- **Railway** - PostgreSQL database + web service
- **Environment Variables** - Secure configuration management

## Project Structure

```
helpme_hub/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── helpme_hub/          # Main Django project
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/             # Authentication & users
├── schoolgroups/         # School group management
├── chats/                # Chat functionality
├── tickets/              # Ticket management
├── knowledge/            # Knowledge base
├── audit/                # Audit logs
├── static/               # CSS, JS, images
└── templates/            # Django templates
```

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL (or use Railway)
- Git

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd helpme_hub
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your local settings
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open http://127.0.0.1:8000 in your browser

For detailed setup instructions, see [DEVELOPMENT.md](DEVELOPMENT.md)

## Deployment

The application is designed to deploy on Railway. See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Railway Setup
1. Create Railway account and connect GitHub
2. Create PostgreSQL database service
3. Create web service and link to database
4. Set environment variables in Railway dashboard
5. Deploy automatically on git push

## Development Phases

The project is built in phases:

- **Phase 0** ✅ - Project blueprint and architecture
- **Phase 1** ✅ - Foundation (authentication, base templates)
- **Phase 2** ✅ - School group approval system
- **Phase 3** ✅ - Chat functionality
- **Phase 4** ✅ - Ticket escalation and management
- **Phase 5** ✅ - Knowledge base and audit logs
- **Phase 6** ✅ - Superadmin management features
- **Phase 7** ✅ - Stripe payment integration
- **Phase 8** ✅ - Comprehensive testing
- **Phase 9** ✅ - Production polish (email notifications, markdown rendering)

See [PHASE_0_BLUEPRINT.md](PHASE_0_BLUEPRINT.md) for complete architecture details.

## Security

- All API keys and secrets stored in environment variables
- Never commit `.env` files to Git
- CSRF protection on all forms
- Role based access control
- School group data isolation
- Secure session management

See [SECURITY.md](SECURITY.md) for security best practices.

## Contributing

This is a private project. For internal development guidelines, see [DEVELOPMENT.md](DEVELOPMENT.md).

## License

See [LICENSE](LICENSE) for license information.

## Documentation

- [Phase 0 Blueprint](PHASE_0_BLUEPRINT.md) - Complete project architecture
- [Architecture & Design](ARCHITECTURE_DESIGN.md) - UI/UX and system design
- [Development Guide](DEVELOPMENT.md) - Local setup and development
- [Deployment Guide](DEPLOYMENT.md) - Production deployment

## Support

For issues or questions, contact the development team.

---

**Built with ❤️ for modern IT support**


