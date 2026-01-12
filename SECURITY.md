# Security Policy - HelpMe Hub

## Supported Versions

We provide security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.5.x   | :white_check_mark: |
| 0.4.x   | :white_check_mark: |
| < 0.4   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please do the following:

1. **Do NOT** create a public GitHub issue
2. Email the security team directly (if available)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## Security Best Practices

### For Developers

1. **Never Commit Secrets**
   - API keys, passwords, and secrets must be in environment variables
   - Always use `.env` files (excluded from Git)
   - Never hardcode credentials

2. **Environment Variables**
   - Use `.env.example` as a template
   - Never commit actual `.env` files
   - Use Railway environment variables for production

3. **Dependencies**
   - Keep dependencies up to date
   - Review `requirements.txt` regularly
   - Use `pip list --outdated` to check for updates

4. **Database Security**
   - Use strong database passwords
   - Never expose database URLs in code
   - Use connection pooling in production
   - Regular backups

5. **Authentication**
   - Use Django's built-in authentication
   - Enforce strong passwords
   - Implement rate limiting for login attempts
   - Use HTTPS in production (Railway default)

6. **Authorization**
   - Always check user roles before allowing access
   - Verify school group membership
   - Never trust user input for school group selection
   - Use Django's permission system

7. **Input Validation**
   - Validate all user inputs
   - Sanitize user-generated content
   - Use Django's form validation
   - Protect against SQL injection (use ORM)

8. **Session Security**
   - Use secure session cookies
   - Set appropriate session timeout
   - Regenerate session on login
   - Use CSRF protection on all forms

### For Deployment

1. **Production Settings**
   - `DEBUG=False` in production
   - `ALLOWED_HOSTS` only includes your domains
   - Strong `SECRET_KEY` (unique per environment)
   - HTTPS only (Railway default)

2. **Environment Variables**
   - Store all secrets in Railway environment variables
   - Never log sensitive information
   - Rotate secrets regularly
   - Use different secrets for dev/staging/production

3. **Database**
   - Use strong database credentials
   - Limit database access to application only
   - Enable database backups
   - Monitor database access logs

4. **Static Files**
   - Serve static files via WhiteNoise or CDN
   - Use HTTPS for all static assets
   - Set appropriate cache headers

## Security Checklist

Before deploying to production:

- [ ] `DEBUG=False`
- [ ] Strong `SECRET_KEY` set
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] All API keys in environment variables (not in code)
- [ ] Database credentials secure
- [ ] HTTPS enabled
- [ ] CSRF protection enabled
- [ ] XSS protection enabled
- [ ] SQL injection prevention (using ORM)
- [ ] Rate limiting configured
- [ ] Error messages don't expose sensitive info
- [ ] Logs don't contain sensitive data
- [ ] Dependencies are up to date
- [ ] Security headers configured

## Known Security Considerations

### School Group Isolation

- Always verify school group membership before data access
- Never trust `school_group_id` from user input
- Derive school group from user's membership
- Use middleware/decorators to enforce isolation

### Role Based Access

- Check user role on every request
- Verify permissions before allowing actions
- Use Django's permission system
- Log unauthorized access attempts

### Data Protection

- Encrypt sensitive data at rest (database)
- Use HTTPS for data in transit
- Implement proper access controls
- Regular security audits

## Security Updates

We regularly update dependencies to address security vulnerabilities. Always:

1. Review security advisories for Django and dependencies
2. Update `requirements.txt` with security patches
3. Test updates in development before production
4. Monitor Django security releases: https://www.djangoproject.com/weblog/

## Reporting Security Issues

Security issues should be reported privately. Public disclosure should only occur after the issue has been addressed and a patch is available.

## Security Resources

- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security](https://python.readthedocs.io/en/latest/library/security.html)


