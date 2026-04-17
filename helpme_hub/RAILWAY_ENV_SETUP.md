# Railway Environment Setup

Use this checklist when deploying the Django web service on Railway.

## 1) Configure database variables on the web service

In the **web service** variables (not in local `.env`), create:

- `DATABASE_URL` = **Reference** to Postgres `DATABASE_URL` (preferred)

Alternative (if needed):

- `DATABASE_URL` = **Reference** to Postgres `DATABASE_PUBLIC_URL`

Do not paste unresolved placeholders or host-less values. A valid value must look like:

`postgresql://user:password@host:port/dbname`

## 2) Project Shared Variables (important)

If you use **Project → Settings → Shared Variables**, do **not** paste a literal Postgres URL that is missing `host:port` (for example `postgresql://user:pass@:/railway`). That breaks every service that inherits those variables.

Prefer either:

- **Variable references** (recommended): `DATABASE_URL="${{Postgres.DATABASE_PUBLIC_URL}}"` and the same for `DATABASE_PRIVATE_URL` if you need it, or
- Remove database keys from Shared Variables and set them only on the **web** and **Postgres** services.

Also add **`DATABASE_PUBLIC_URL`** on the web service referencing Postgres `DATABASE_PUBLIC_URL` if your other URLs are still host-less.

## 3) Remove conflicting variables

If present and invalid, clear or fix:

- `DATABASE_PRIVATE_URL`
- `DATABASE_PUBLIC_URL`
- any host-less form like `postgresql://user:pass@/dbname`

## 4) Optional split-variable fallback

If you prefer split vars, all of these must be set as Postgres references:

- `POSTGRES_HOST`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`
- `POSTGRES_PORT`

(`PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, `PGPORT` are also supported.)

## 5) Redeploy and validate

After saving variables:

1. Redeploy the web service.
2. Verify logs no longer include:
   - `ImproperlyConfigured: Database URL variable(s) are set but have no hostname`
3. If you see that error mentioning **`DATABASE_PUBLIC_URL`** only: your web service has a **bad or host-less** public URL (often a mistaken Shared Variable or manual paste). **Delete `DATABASE_PUBLIC_URL`** on the web service unless it is a proper Railway reference, and set **`DATABASE_URL`** to a **Reference** from Postgres → `DATABASE_URL` (must contain `@host:port/`).
4. Run migrations once startup is healthy:
   - `python manage.py migrate --noinput`

