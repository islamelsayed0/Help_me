# Phase 0: Project Blueprint - HelpMe Hub

## High Level Goal
Build a modern, calm, enterprise and school friendly IT support portal in dark mode only.

## Technology Stack (Default Proposal)

**Backend:**
- Django 4.2+ (Python web framework)
- PostgreSQL (database)
- Django Allauth (authentication with Google OAuth support)
- Gunicorn (WSGI server for production)
- WhiteNoise (static file serving)

**Frontend:**
- Django Templates (server-rendered HTML)
- Tailwind CSS (via CDN for styling)
- Vanilla JavaScript (for interactive features)
- No React

**Hosting:**
- Railway (PostgreSQL database + web service)

**Key Libraries:**
- `django-allauth` - Authentication (traditional + Google OAuth)
- `psycopg2-binary` - PostgreSQL adapter
- `dj-database-url` - Database URL parsing
- `python-decouple` - Environment variables
- `gunicorn` - Production server
- `whitenoise` - Static files

---

## Final Pages List

### Public Pages (Unauthenticated)
1. **Loading Page** (`/loading/`)
   - Initial app load screen
   - Shows during authentication check

2. **Login Page** (`/accounts/login/`)
   - Email/password login
   - Google OAuth login button
   - Link to registration

3. **Registration Page** (`/accounts/register/`)
   - Create account form
   - Google OAuth signup button
   - Link to login

### User Role Pages

4. **Pending Approval Page** (`/pending/`)
   - Shown when user has no school group membership
   - Display join request status
   - Show "Request to Join School Group" button if no request exists

5. **User Dashboard** (`/dashboard/`)
   - Overview of user's tickets
   - Quick actions
   - Recent activity

6. **Chat List** (`/chats/`)
   - List of user's active chats
   - Create new chat button
   - Show chat status (active, escalated, resolved)

7. **Chat Detail** (`/chats/<chat_id>/`)
   - Chat messages display
   - Message input area
   - Escalate to ticket button (if not already escalated)
   - Chat status indicator

8. **My Tickets** (`/tickets/`)
   - List of tickets created by user (from escalated chats)
   - Filter by status
   - Link to ticket detail

9. **Ticket Detail** (`/tickets/<ticket_id>/`)
   - Ticket information
   - Linked chat transcript
   - Resolution notes (if closed)
   - Status display

10. **Knowledge Base** (`/knowledge/`)
    - Browse published articles
    - Search functionality
    - Category filtering
    - Article detail view

11. **Profile** (`/profile/`)
    - User information
    - School group membership
    - Dark mode preference
    - Account settings

### Admin Role Pages

12. **Admin Dashboard** (`/admin/dashboard/`)
    - Overview statistics
    - Recent activity
    - Quick actions

13. **Admin Chat Inbox** (`/admin/chats/`)
    - List of all chats in admin's school group
    - Filter by status (active, escalated, resolved)
    - Unread indicator
    - Assign to admin option

14. **Admin Chat Detail** (`/admin/chats/<chat_id>/`)
    - Chat messages display
    - Reply to chat
    - Assign chat
    - Escalate to ticket button
    - Mark as resolved

15. **Admin Tickets Board** (`/admin/tickets/board/`)
    - Kanban-style board view
    - Columns: Open, In Progress, Resolved, Closed
    - Drag and drop or click to change status
    - Filter by assignee
    - Quick view of ticket details

16. **Admin Ticket Detail** (`/admin/tickets/<ticket_id>/`)
    - Full ticket information
    - Linked chat transcript
    - Change status
    - Assign to admin
    - Add resolution notes
    - Close ticket

17. **Join Requests Management** (`/admin/joinrequests/`)
    - List of pending join requests for school group
    - Accept/Deny actions
    - View request details
    - Bulk actions

18. **Knowledge Base Management** (`/admin/knowledge/`)
    - List of articles (draft and published)
    - Create/edit articles
    - Publish/unpublish articles
    - Category management

19. **Admin Profile** (`/admin/profile/`)
    - Admin information
    - School group management
    - Settings

### Superadmin Role Pages

20. **Superadmin Dashboard** (`/superadmin/dashboard/`)
    - System overview
    - All school groups statistics
    - Recent activity across all groups

21. **School Groups Management** (`/superadmin/schoolgroups/`)
    - List of all school groups
    - Create/edit school groups
    - View group members
    - Group settings

22. **Roles Management** (`/superadmin/roles/`)
    - Manage user roles
    - Assign roles to users
    - View role assignments

23. **Audit Logs** (`/superadmin/auditlogs/`)
    - View all audit log entries
    - Filter by action type, user, school group, date
    - Export logs

24. **System Settings** (`/superadmin/settings/`)
    - Global system settings
    - Feature toggles
    - Configuration management

25. **Superadmin Profile** (`/superadmin/profile/`)
    - Superadmin information
    - System access

---

## Data Model Tables and Relationships

### Core Tables

#### 1. User (extends Django AbstractUser)
```python
Fields:
- id (PK)
- username
- email
- first_name
- last_name
- role (choices: 'user', 'admin', 'superadmin')
- dark_mode_preference (boolean, default=True)
- created_at
- updated_at

Relationships:
- One-to-Many: SchoolGroupMembership
- One-to-Many: Chat (as creator)
- One-to-Many: Ticket (as creator)
- One-to-Many: Article (as author)
- One-to-Many: AuditLog (as actor)
```

#### 2. SchoolGroup
```python
Fields:
- id (PK)
- name (unique)
- description
- is_active (boolean, default=True)
- created_at
- updated_at

Relationships:
- One-to-Many: SchoolGroupMembership
- One-to-Many: Chat
- One-to-Many: Ticket
- One-to-Many: Article
- One-to-Many: JoinRequest
```

#### 3. SchoolGroupMembership
```python
Fields:
- id (PK)
- user_id (FK -> User)
- school_group_id (FK -> SchoolGroup)
- status (choices: 'pending', 'accepted', 'denied')
- joined_at (nullable, set when accepted)
- created_at
- updated_at

Unique Constraint:
- (user_id, school_group_id) - one membership per user per group

Relationships:
- Many-to-One: User
- Many-to-One: SchoolGroup
```

#### 4. JoinRequest
```python
Fields:
- id (PK)
- user_id (FK -> User)
- school_group_id (FK -> SchoolGroup)
- status (choices: 'pending', 'accepted', 'denied')
- requested_at
- reviewed_at (nullable)
- reviewed_by_id (FK -> User, nullable, admin who reviewed)
- notes (text, nullable, admin notes)
- created_at
- updated_at

Relationships:
- Many-to-One: User (requester)
- Many-to-One: SchoolGroup
- Many-to-One: User (reviewer, admin)
```

#### 5. Chat
```python
Fields:
- id (PK)
- user_id (FK -> User, creator)
- school_group_id (FK -> SchoolGroup)
- assigned_to_id (FK -> User, nullable, admin assigned)
- status (choices: 'active', 'escalated', 'resolved', 'closed')
- escalated_at (nullable)
- resolved_at (nullable)
- created_at
- updated_at

Relationships:
- Many-to-One: User (creator)
- Many-to-One: User (assigned admin)
- Many-to-One: SchoolGroup
- One-to-Many: ChatMessage
- One-to-One: Ticket (if escalated)
```

#### 6. ChatMessage
```python
Fields:
- id (PK)
- chat_id (FK -> Chat)
- sender_id (FK -> User)
- sender_type (choices: 'user', 'admin')
- content (text)
- is_read (boolean, default=False)
- created_at

Relationships:
- Many-to-One: Chat
- Many-to-One: User (sender)
```

#### 7. Ticket
```python
Fields:
- id (PK)
- chat_id (FK -> Chat, nullable, if created from chat)
- user_id (FK -> User, creator)
- school_group_id (FK -> SchoolGroup)
- assigned_to_id (FK -> User, nullable, admin assigned)
- title
- description
- status (choices: 'open', 'in_progress', 'resolved', 'closed')
- priority (choices: 'low', 'medium', 'high', 'urgent', default='medium')
- resolution_notes (text, nullable)
- resolved_at (nullable)
- closed_at (nullable)
- created_at
- updated_at

Relationships:
- Many-to-One: Chat (source chat)
- Many-to-One: User (creator)
- Many-to-One: User (assigned admin)
- Many-to-One: SchoolGroup
```

#### 8. Article (Knowledge Base)
```python
Fields:
- id (PK)
- school_group_id (FK -> SchoolGroup, nullable, if group-specific)
- author_id (FK -> User)
- title
- content (text)
- category
- tags (many-to-many or JSON field)
- status (choices: 'draft', 'published')
- view_count (integer, default=0)
- helpful_votes (integer, default=0)
- published_at (nullable)
- created_at
- updated_at

Relationships:
- Many-to-One: SchoolGroup (optional, for group-specific articles)
- Many-to-One: User (author)
```

#### 9. AuditLog
```python
Fields:
- id (PK)
- actor_id (FK -> User, who performed action)
- school_group_id (FK -> SchoolGroup, nullable, if group-specific)
- action_type (choices: 'join_request_created', 'join_request_accepted', 
               'join_request_denied', 'role_changed', 'ticket_closed', 
               'ticket_assigned', 'article_published', 'settings_changed')
- resource_type (string, e.g., 'JoinRequest', 'Ticket', 'User')
- resource_id (integer, ID of affected resource)
- description (text, human-readable description)
- metadata (JSON field, additional context)
- created_at

Relationships:
- Many-to-One: User (actor)
- Many-to-One: SchoolGroup (context)
```

### Relationship Diagram

```
User
├── SchoolGroupMembership ──> SchoolGroup
├── JoinRequest ──> SchoolGroup
├── Chat ──> SchoolGroup
│   └── ChatMessage
│   └── Ticket (if escalated)
├── Ticket ──> SchoolGroup
├── Article ──> SchoolGroup (optional)
└── AuditLog ──> SchoolGroup (context)

SchoolGroup
├── SchoolGroupMembership ──> User
├── JoinRequest ──> User
├── Chat ──> User
├── Ticket ──> User
└── Article ──> User
```

---

## Permission Rules

### Role Definitions

1. **User**
   - Can request to join school groups
   - Can create chats in their school group
   - Can view their own chats
   - Can escalate their chats to tickets
   - Can view their own tickets
   - Can view published knowledge base articles
   - Cannot access admin or superadmin pages

2. **Admin**
   - All User permissions
   - Can view all chats in their school group
   - Can reply to chats in their school group
   - Can assign chats to themselves or other admins in group
   - Can view and manage all tickets in their school group
   - Can change ticket status
   - Can assign tickets
   - Can close tickets with resolution notes
   - Can manage join requests for their school group
   - Can create/edit/publish knowledge base articles for their group
   - Cannot access superadmin pages
   - Cannot manage other school groups

3. **Superadmin**
   - All Admin permissions across all school groups
   - Can manage school groups (create, edit, delete)
   - Can manage user roles
   - Can view audit logs across all school groups
   - Can manage system settings
   - Can publish articles globally (not group-specific)

### Data Isolation Rules

1. **School Group Isolation**
   - Users can only see data from school groups they are members of
   - Admins can only manage data in their school group(s)
   - Superadmins can see all data but should filter by school group in UI
   - All queries must filter by school group membership

2. **Enforcement Points**
   - **Chats:** Filter by user's school group membership
   - **Tickets:** Filter by user's school group membership
   - **Articles:** Show group-specific articles + global articles (if any)
   - **Join Requests:** Admins only see requests for their school group
   - **Audit Logs:** Filter by school group context

3. **Membership Verification**
   - Always verify membership status = 'accepted' before allowing access
   - Never trust school_group_id from user input
   - Always derive school group from user's membership
   - Use middleware or decorators to enforce isolation

---

## Chat Lifecycle States

### State Flow

```
[New Chat Created]
    ↓
[active] ──> User and Admin can exchange messages
    ↓
    ├──> [escalated] ──> When user clicks "Escalate to Ticket"
    │                      Creates linked ticket
    │                      Chat becomes read-only reference
    │
    └──> [resolved] ──> When admin marks chat as resolved
                         (no ticket created)
    ↓
[closed] ──> Final state, archived
```

### State Definitions

1. **active**
   - Chat is open and ongoing
   - User and admin can send messages
   - Can be escalated to ticket
   - Can be marked as resolved

2. **escalated**
   - User has escalated chat to ticket
   - Ticket is created and linked
   - Chat becomes read-only
   - Further communication happens via ticket
   - Cannot be changed back to active

3. **resolved**
   - Admin marked chat as resolved
   - No ticket was created
   - Chat is closed
   - User can see resolution

4. **closed**
   - Final archived state
   - No further actions possible
   - Historical record only

### State Transitions

| From State | To State | Trigger | Who Can Trigger |
|------------|----------|---------|-----------------|
| active | escalated | Escalate button | User |
| active | resolved | Mark as resolved | Admin |
| escalated | closed | Ticket closed | System (when linked ticket closes) |
| resolved | closed | Archive | Admin or System |

---

## Ticket Lifecycle States

### State Flow

```
[Ticket Created from Chat Escalation]
    ↓
[open] ──> New ticket, not yet assigned
    ↓
[in_progress] ──> Assigned to admin, work in progress
    ↓
[resolved] ──> Admin adds resolution notes
    ↓
[closed] ──> Final state, archived
```

### State Definitions

1. **open**
   - Ticket just created
   - Not yet assigned to admin
   - Waiting for admin to pick up
   - Can be assigned

2. **in_progress**
   - Ticket assigned to admin
   - Admin is working on it
   - Can add updates
   - Can be resolved

3. **resolved**
   - Admin has added resolution notes
   - Issue is resolved
   - User can see resolution
   - Can be closed

4. **closed**
   - Final archived state
   - No further actions possible
   - Historical record only

### State Transitions

| From State | To State | Trigger | Who Can Trigger |
|------------|----------|---------|-----------------|
| open | in_progress | Assign to admin | Admin |
| open | resolved | Resolve directly | Admin |
| in_progress | resolved | Add resolution notes | Admin |
| resolved | closed | Close ticket | Admin |
| Any | closed | Close directly | Admin (with resolution notes) |

### Priority Levels

- **low** - Non-urgent, can wait
- **medium** - Normal priority (default)
- **high** - Important, needs attention soon
- **urgent** - Critical, immediate attention required

---

## Route Protection Rules

### Authentication Required
- All pages except: Loading, Login, Registration
- Enforced via Django `@login_required` decorator

### Role-Based Access
- User pages: `/dashboard/`, `/chats/`, `/tickets/`, `/knowledge/`, `/profile/`
- Admin pages: `/admin/*` (requires role='admin')
- Superadmin pages: `/superadmin/*` (requires role='superadmin')

### Membership Required
- All support features require accepted school group membership
- Users without membership see pending approval page
- Enforced via custom decorator or middleware

### Data Access
- Users can only access their own chats/tickets
- Admins can access all chats/tickets in their school group
- Superadmins can access all data (with school group filtering in UI)

---

## File Naming Conventions

### Rules
- No hyphens in file names, routes, UI text, or comments
- Use underscores for file names: `chat_detail.html`, `ticket_list.html`
- Use underscores for route names: `chat_detail`, `ticket_list`
- Use camelCase or underscores for JavaScript: `chatDetail`, `chat_detail`
- Use PascalCase for Python classes: `ChatDetail`, `TicketList`

### Examples
- ✅ `chat_detail.html` (not `chat-detail.html`)
- ✅ `ticket_list_view.py` (not `ticket-list-view.py`)
- ✅ Route: `chat_detail` (not `chat-detail`)
- ✅ UI Text: "Chat Detail" (not "Chat-Detail")
- ✅ Comment: `# Get chat details` (not `# Get chat-details`)

---

## Security Considerations

### Authorization Checks
- Every view must check user role
- Every view must check school group membership
- Every view must verify data ownership (for users) or group access (for admins)
- Never trust user input for school group selection

### Data Validation
- Validate all form inputs
- Sanitize user-generated content
- Use Django's built-in validators
- Clear error messages for users

### Session Security
- Secure session cookies
- CSRF protection on all forms
- XSS protection
- SQL injection prevention (Django ORM)

### API Keys and Secrets Management
- **Never commit API keys, secrets, or credentials to Git**
- All sensitive values stored in environment variables
- Use `.env` file for local development (added to `.gitignore`)
- Use Railway environment variables for production
- Required secrets:
  - `SECRET_KEY` - Django secret key
  - `DATABASE_URL` - PostgreSQL connection string
  - `GOOGLE_OAUTH2_CLIENT_ID` - Google OAuth client ID
  - `GOOGLE_OAUTH2_CLIENT_SECRET` - Google OAuth client secret
  - `DEBUG` - Debug mode (False in production)
  - `ALLOWED_HOSTS` - Allowed hostnames
- Create `.env.example` file with placeholder values (committed to Git)
- `.gitignore` must exclude:
  - `.env` files
  - `*.pyc` files
  - `__pycache__/` directories
  - Database files
  - Static files (collected)
  - Media files
  - IDE configuration files

---

## Database Migration Strategy

### Approach
- Use Django migrations for all schema changes
- Create migrations incrementally per phase
- Test migrations on development before production
- Keep migrations reversible when possible
- Document any data migrations

### Migration Files
- Phase 1: User, SchoolGroup, SchoolGroupMembership
- Phase 2: JoinRequest
- Phase 3: Chat, ChatMessage
- Phase 4: Ticket
- Phase 5: Article, AuditLog

---

## Next Steps After Phase 0 Approval

Once you approve this blueprint by saying "next", I will proceed to:

**Phase 1: Foundation**
- Set up Django project structure
- Configure `.gitignore` (exclude `.env`, API keys, secrets)
- Create `.env.example` template (with placeholder values, committed to Git)
- Configure PostgreSQL database
- Set up authentication (traditional + Google OAuth)
- Create role-based route protection
- Build dark mode base templates
- Create navigation shells
- Set up Railway deployment configuration
- Configure environment variable management (python-decouple)

---

## Summary

This blueprint defines:
- ✅ 25 final pages across 3 roles
- ✅ 9 core data model tables with relationships
- ✅ Permission rules for user, admin, superadmin
- ✅ Data isolation rules by school group
- ✅ Chat lifecycle (4 states: active, escalated, resolved, closed)
- ✅ Ticket lifecycle (4 states: open, in_progress, resolved, closed)
- ✅ Security and validation rules
- ✅ File naming conventions (no hyphens)
- ✅ Migration strategy

Ready for your approval to proceed to Phase 1.

