# DCFT Controlled Cloud Staging Runbook

Purpose: prepare a reversible staging deploy without turning DCFT into a production-mass service.

## Required Services

- Backend service with the current repository commit.
- Frontend service pointing only to the staging backend URL.
- PostgreSQL database dedicated to staging.
- Persistent storage for audit exports and operational evidence if the platform supports it.

## Required Secrets

- `DCFT_DATABASE_URL`
- `DCFT_JWT_SECRET`
- `DCFT_ADMIN_PASSWORD`
- `DCFT_APP_ENV=staging`
- `DCFT_DB_AUTO_MIGRATE=true`
- `DCFT_AI_PROVIDER_ENABLED=false`
- `DCFT_OCR_ENABLED=false`
- Frontend `VITE_DCFT_API_URL=https://<staging-backend>`

Use `.env.staging.example` only as a template. Store real values in the cloud provider secret manager.

## Pre-Deploy Checks

- Run `pytest -q`.
- Run `npm run build` inside `apps/frontend`.
- Run Alembic against the staging database.
- Verify `/health`, `/runtime/status`, `/onboarding/status`, `/subscriptions/plans`.
- Confirm `production_ready=false` until secrets, backups, monitoring, and rollback are verified.
- Run `python tools/validate_staging_config.py --env-file .env.staging` locally before entering secrets in the provider.

## Rollback

- Keep the previous backend and frontend builds available.
- Take a database backup before migration.
- Do not enable external AI or OCR during staging.
- Disable public onboarding if abuse monitoring is not in place.

## Post-Deploy Smoke

- Create one staging tenant through `/onboarding/tenants`.
- Login as the new tenant admin.
- Confirm tenant-scoped `/dashboard/summary`.
- Create one alert, one document metadata record, and one workflow.
- Confirm `/analytics/summary` reflects onboarding and first business signal.
- Confirm audit events are tenant scoped.
- Run `python tools/staging_smoke.py --api-url https://<staging-backend>`.
- Run `node tools/validate_frontend_viewports.js` with `DCFT_FRONTEND_URL` and `DCFT_STAGING_API_URL` set to staging URLs.

## Go / No-Go Boundaries

- No real customer data until backups and retention policy are verified.
- No production claims while `production_ready=false`.
- No payment collection until subscription limits, downgrade behavior, and support processes are validated with real users.
