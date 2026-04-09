# Railway Environment Setup

Use this checklist when deploying the Django web service on Railway.

## 1) Configure database variables on the web service

In the **web service** variables (not in local `.env`), create:

- `DATABASE_URL` = **Reference** to Postgres `DATABASE_URL` (preferred)

Alternative (if needed):

- `DATABASE_URL` = **Reference** to Postgres `DATABASE_PUBLIC_URL`

Do not paste unresolved placeholders or host-less values. A valid value must look like:

`postgresql://user:password@host:port/dbname`

## 2) Remove conflicting variables

If present and invalid, clear or fix:

- `DATABASE_PRIVATE_URL`
- `DATABASE_PUBLIC_URL`
- any host-less form like `postgresql://user:pass@/dbname`

## 3) Optional split-variable fallback

If you prefer split vars, all of these must be set as Postgres references:

- `POSTGRES_HOST`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_PORT`

(`PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, `PGPORT` are also supported.)

## 4) Redeploy and validate

After saving variables:

1. Redeploy the web service.
2. Verify logs no longer include:
   - `ImproperlyConfigured: Database URL variable(s) are set but have no hostname`
3. Run migrations once startup is healthy:
   - `python manage.py migrate --noinput`

