# Development Guide - HelpMe Hub

## Local Development Setup

### Prerequisites

- **Python 3.11+** - Check with `python --version`
- **PostgreSQL** (optional for local dev, can use SQLite)
- **Git** - Version control
- **Virtual Environment** - Python virtual environment tool

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd helpme_hub
```

### Step 2: Create Virtual Environment

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Environment Variables

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file with your local settings:**
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   
   # For local development, you can use SQLite (leave DATABASE_URL empty)
   # Or use PostgreSQL:
   DATABASE_URL=postgresql://user:password@localhost:5432/helpmehub
   
   # Google OAuth (optional for local dev)
   GOOGLE_OAUTH2_CLIENT_ID=your-client-id
   GOOGLE_OAUTH2_CLIENT_SECRET=your-client-secret
   ```

3. **Generate Django secret key:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Copy the output to `SECRET_KEY` in `.env`

### Step 5: Database Setup

**Option A: SQLite (Easiest for local dev)**
- No additional setup needed
- Django will create `db.sqlite3` automatically

**Option B: PostgreSQL**
1. Install PostgreSQL locally
2. Create database:
   ```sql
   CREATE DATABASE helpmehub;
   ```
3. Update `DATABASE_URL` in `.env`

### Step 6: Run Migrations

```bash
python manage.py migrate
```

### Step 7: Create Superuser

```bash
python manage.py createsuperuser
```
Follow prompts to create admin account.

### Step 8: Collect Static Files (if needed)

```bash
python manage.py collectstatic --noinput
```

### Step 9: Run Development Server

```bash
python manage.py runserver
```

Access the application at: http://127.0.0.1:8000

## Development Workflow

### Running the Server

```bash
# Standard run
python manage.py runserver

# Run on specific port
python manage.py runserver 8080

# Run on all interfaces
python manage.py runserver 0.0.0.0:8000
```

### Creating Migrations

When you modify models:

```bash
# Create migration files
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### Creating Django Apps

```bash
python manage.py startapp app_name
```

### Django Shell

```bash
# Interactive Python shell with Django context
python manage.py shell

# Example usage:
from accounts.models import User
User.objects.all()
```

### Creating Superuser

```bash
python manage.py createsuperuser
```

### Database Management

```bash
# Access Django admin
# Visit: http://127.0.0.1:8000/admin/

# Reset database (WARNING: deletes all data)
python manage.py flush

# Show SQL for migrations
python manage.py sqlmigrate app_name migration_number
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Use 4 spaces for indentation
- Maximum line length: 88 characters (Black default)
- Use descriptive variable names
- Add docstrings to functions and classes

### Django Best Practices

- Use Django's built-in features when possible
- Keep views thin, logic in models or services
- Use Django ORM, avoid raw SQL
- Use Django's authentication system
- Follow Django naming conventions

### File Naming

- **No hyphens** in file names, routes, UI text, or comments
- Use underscores: `chat_detail.html`, `ticket_list.py`
- Use camelCase for JavaScript: `chatDetail`
- Use PascalCase for Python classes: `ChatDetail`

## Testing

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts

# Run specific test
python manage.py test accounts.tests.test_views.TestLoginView

# Run with verbosity
python manage.py test --verbosity=2
```

### Manual Testing Checklist

After each phase, manually test:
1. Authentication (login, register, Google OAuth)
2. Role based access (user, admin, superadmin)
3. School group isolation
4. Feature functionality
5. Responsive design (mobile, tablet, desktop)
6. Dark mode appearance

## Debugging

### Django Debug Toolbar (Optional)

Add to `INSTALLED_APPS` in development:
```python
INSTALLED_APPS = [
    # ...
    'debug_toolbar',
]
```

### Logging

Check Django logs in console output. For production logging, configure in `settings.py`.

### Common Issues

**Migration errors:**
```bash
# Reset migrations (WARNING: data loss)
python manage.py migrate app_name zero
python manage.py migrate
```

**Static files not loading:**
```bash
python manage.py collectstatic
```

**Import errors:**
- Check virtual environment is activated
- Verify all dependencies installed: `pip list`
- Check Python path

## Git Workflow

### Before Committing

1. **Check what will be committed:**
   ```bash
   git status
   git diff
   ```

2. **Ensure `.env` is not committed:**
   ```bash
   git status | grep .env
   # Should show nothing or show .env in untracked
   ```

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Be descriptive but concise
- Reference issue numbers if applicable

## Environment Variables Reference

### Required

- `SECRET_KEY` - Django secret key
- `DEBUG` - True for development, False for production
- `ALLOWED_HOSTS` - Comma separated hostnames

### Database

- `DATABASE_URL` - PostgreSQL connection string (optional, can use SQLite locally)

### Google OAuth (Optional)

- `GOOGLE_OAUTH2_CLIENT_ID` - From Google Cloud Console
- `GOOGLE_OAUTH2_CLIENT_SECRET` - From Google Cloud Console

### Email (Optional)

- `EMAIL_BACKEND` - Email backend (console for dev)
- `EMAIL_HOST` - SMTP server
- `EMAIL_PORT` - SMTP port
- `EMAIL_USE_TLS` - Use TLS
- `EMAIL_HOST_USER` - Email username
- `EMAIL_HOST_PASSWORD` - Email password

## Next Steps

After local setup is complete:
1. Review [PHASE_0_BLUEPRINT.md](PHASE_0_BLUEPRINT.md)
2. Start Phase 1 development
3. Follow phase by phase approach
4. Test after each phase

## Getting Help

- Check Django documentation: https://docs.djangoproject.com/
- Review project documentation in `/docs` (if available)
- Check error messages in console output
- Review [ARCHITECTURE_DESIGN.md](ARCHITECTURE_DESIGN.md) for design details


