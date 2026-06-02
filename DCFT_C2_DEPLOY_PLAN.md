# DCFT C.2 Deploy Plan

## Scope

Etapa C.2: real staging deployment on Render using the existing PostgreSQL database `dcft-db`.

Out of scope:

- No OCR activation.
- No embeddings activation.
- No new product functionality.
- No production classification.

## Source State

- Repository: `C:\Users\admin\dcft-knowledge-core`
- Branch: `main`
- Commit prepared and pushed: `0a0ecb5`
- Previous commit before C.2 push: `794eb3c`

## Render Blueprint Configuration

Backend service:

- Name: `dcft-backend`
- Runtime: Python
- Build command: `pip install --upgrade pip && pip install -r requirements.txt`
- Pre-deploy command: `PYTHONPATH=apps/backend alembic upgrade head`
- Start command: `PYTHONPATH=apps/backend uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Database env: `DCFT_DATABASE_URL` from existing Render database `dcft-db`
- SSL: `DCFT_DATABASE_SSL=true`
- Runtime migrations: `DCFT_DB_AUTO_MIGRATE=false`
- AI/OCR: disabled

Frontend service:

- Name: `dcft-frontend`
- Runtime: static
- Root directory: `apps/frontend`
- Build command: `npm ci && npm run build`
- Publish directory: `dist`
- API URL: `https://dcft-backend.onrender.com`

Expected staging URLs:

- Backend: `https://dcft-backend.onrender.com`
- Frontend: `https://dcft-frontend.onrender.com`

## Required Render Resource

The database `dcft-db` must already exist in the same Render workspace. The Blueprint references it with:

```yaml
fromDatabase:
  name: dcft-db
  property: connectionString
```

The previous `dcft-postgres` database declaration was removed to avoid creating a second database.

## Required Render Action

Because no Render CLI/API token/session is available in this environment, the remaining cloud action must be performed in Render:

1. Sign in to Render.
2. Create or sync Blueprint from GitHub repo `danielglezsolucionador-boop/DCFT`.
3. Confirm existing database `dcft-db` is in the same workspace.
4. Apply Blueprint commit `0a0ecb5`.
5. Let backend pre-deploy Alembic run.
6. Let backend and frontend deploy.

## Rollback Plan

If the Render deploy fails before migration:

- Revert backend/frontend services to previous successful deploy.
- Revert source to `794eb3c` if needed.
- No database rollback required if Alembic did not run.

If Alembic runs and then backend fails:

- Do not delete `dcft-db`.
- Take a database backup first.
- Revert app deploy to previous build.
- Review whether migration `0002_enterprise_hardening` requires manual rollback.

If frontend fails only:

- Roll back `dcft-frontend` deploy.
- Keep `dcft-backend` and `dcft-db` unchanged.

## Go Criteria

- `/health` returns 200.
- `/runtime/status` returns 200.
- `database.status=ok`.
- `staging_ready=true`.
- Frontend loads and calls backend without CORS errors.
- `tools/staging_smoke.py --api-url https://dcft-backend.onrender.com` passes.
