# Changelog

All notable changes to HelpMe Hub will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 0: Project blueprint and architecture documentation
- Complete data model design with 9 core tables
- Permission rules for user, admin, and superadmin roles
- Chat and ticket lifecycle state definitions
- School group data isolation rules
- Security considerations and API key management
- .gitignore file for protecting secrets
- README.md with project overview
- LICENSE file (MIT)
- DEVELOPMENT.md with local setup guide
- DEPLOYMENT.md with Railway deployment instructions
- Architecture and design documentation
- Responsive design specifications for mobile/tablet/desktop
- Google OAuth authentication design
- Dark mode UI specifications

### Security
- .gitignore configured to exclude .env files and API keys
- Environment variable management strategy
- Secure session and authentication design

## [0.1.0] - 2024-XX-XX (Planned)

### Phase 1: Foundation
- Django project structure
- Authentication system (traditional + Google OAuth)
- Role based route protection
- Dark mode base templates
- Navigation shells
- Railway deployment configuration

## [0.2.0] - 2024-XX-XX (Planned)

### Phase 2: School Group Approval
- School group management
- Join request flow
- Admin approval/denial system
- Pending approval page

## [0.3.0] - 2024-XX-XX (Planned)

### Phase 3: Chat
- Chat creation and messaging
- Admin chat inbox
- Chat detail view
- Real time polling
- Chat transcripts

## [0.4.0] - 2024-XX-XX (Planned)

### Phase 4: Ticket Escalation
- Escalate chat to ticket
- User ticket list and detail
- Admin ticket board (Kanban)
- Ticket status management
- Resolution notes

## [0.5.0] - 2024-XX-XX

### Phase 5: Knowledge Base and Audit
- Knowledge base articles with markdown support
- Draft and published states
- Article categories and tags
- Helpful votes system
- Audit logs with comprehensive tracking
- Superadmin audit log views with filtering and CSV export

## [0.6.0] - 2024-XX-XX

### Phase 6: Superadmin Management Features
- Enhanced superadmin dashboard with system-wide statistics
- School groups management (list, view, edit, members)
- Roles management (list, assign, bulk assign)
- System settings page with configuration display

## [0.7.0] - 2024-XX-XX

### Phase 7: Stripe Integration
- Stripe checkout for plan upgrades (Pro, Enterprise)
- AI Add-On subscription billing ($7/month)
- Stripe webhook handler for subscription lifecycle
- Subscription status management and sync

## [0.8.0] - 2024-XX-XX

### Phase 8: Testing & Quality Assurance
- Comprehensive unit tests for knowledge base (models, views, admin)
- Comprehensive unit tests for audit logs (models, views, export)
- Integration tests for audit logging across app actions

## [0.9.0] - 2024-XX-XX

### Phase 9: Production Polish
- Email notifications for key events (registration, approvals, tickets, chat escalation)
- Markdown rendering for knowledge base articles with syntax highlighting
- Production logging configuration with file rotation
- Enhanced security settings (HSTS, secure cookies)
- Complete feature documentation

---

## Version History

- **0.0.1** - Phase 0: Project blueprint and documentation
- **0.1.0** - Phase 1: Foundation
- **0.2.0** - Phase 2: School groups
- **0.3.0** - Phase 3: Chat
- **0.4.0** - Phase 4: Tickets
- **0.5.0** - Phase 5: Knowledge base and audit
- **0.6.0** - Phase 6: Superadmin management features
- **0.7.0** - Phase 7: Stripe integration
- **0.8.0** - Phase 8: Testing & quality assurance
- **0.9.0** - Phase 9: Production polish


