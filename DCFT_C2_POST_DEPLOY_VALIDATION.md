# DCFT C.2 Post Deploy Validation

## Live URLs Tested

Backend health:

- URL: `https://dcft-backend.onrender.com/health`
- Result: FAIL
- HTTP status: 404

Backend readiness:

- URL: `https://dcft-backend.onrender.com/runtime/status`
- Result: FAIL
- HTTP status: 404

Frontend:

- URL: `https://dcft-frontend.onrender.com`
- Result: FAIL
- HTTP status: 404

## Live Smoke Test

Command:

```powershell
.venv\Scripts\python.exe tools\staging_smoke.py --api-url https://dcft-backend.onrender.com --requests 5
```

Result:

- FAIL
- Error: `RuntimeError: health failed:404`

## Database Validation

Configured database:

- Render database resource expected: `dcft-db`
- Env source: `fromDatabase.name=dcft-db`

Cloud database connection:

- Not validated live because backend service is not live.

Cloud migrations:

- Not confirmed live because backend service is not live.
- Render pre-deploy command is configured to run Alembic:
  `PYTHONPATH=apps/backend alembic upgrade head`

Local migration state:

- Alembic head: `0002_enterprise_hardening`
- Local current: `0002_enterprise_hardening`

## Health / Readiness Criteria

Expected after Render Blueprint sync:

- `/health` status 200
- `/health.database.status=ok`
- `/health.staging_ready=true`
- `/runtime/status` status 200
- `/runtime/status.database.status=ok`
- `/runtime/status.busy_loop=false`

Current:

- Not live. Both backend endpoints return 404.

## Rollback

Because no live Render deploy occurred:

- No cloud rollback was executed.
- No cloud database rollback is required based on current evidence.
- Source rollback, if needed: revert commit `0a0ecb5`.

If Render Blueprint is synced later and fails:

- Roll back backend/frontend deploy in Render.
- Keep `dcft-db`.
- Back up `dcft-db` before any schema rollback.

## Final C.2 Status

- Backend live: NO
- Frontend live: NO
- Database live: NO
- Health live: NO
- Readiness live: NO
- Smoke live: NO
- Source-to-live: NO

## Blocker

Authenticated Render access is required to create or sync the Blueprint. The local environment has no Render CLI, no Render API token, and the dashboard is at the login screen.

## Next Exact Action

In Render dashboard:

1. Log in.
2. Open Blueprints.
3. Connect GitHub repo `danielglezsolucionador-boop/DCFT`.
4. Select commit `0a0ecb5` or latest `main`.
5. Confirm existing PostgreSQL resource `dcft-db`.
6. Apply Blueprint.
7. Re-run live validation.

## Result

¿C.2 COMPLETADA? NO

¿DCFT STAGING_READY? NO
