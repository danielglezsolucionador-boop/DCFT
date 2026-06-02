# DCFT C.2 Deploy Execution

## Actions Executed

1. Audited `render.yaml`.
2. Found database mismatch:
   - Previous reference: `dcft-postgres`
   - Required target: existing `dcft-db`
3. Updated `render.yaml`:
   - `DCFT_DATABASE_URL` now references `dcft-db`.
   - Removed `databases:` block to avoid creating `dcft-postgres`.
   - Set frontend API URL to `https://dcft-backend.onrender.com`.
   - Set backend CORS/frontend origin to `https://dcft-frontend.onrender.com`.
   - Set `DCFT_ADMIN_PASSWORD` and `DCFT_JWT_SECRET` to Render `generateValue: true`.
   - Kept `DCFT_AI_PROVIDER_ENABLED=false`.
   - Kept `DCFT_OCR_ENABLED=false`.
4. Validated local backend with project virtualenv.
5. Validated frontend build.
6. Validated staging environment shape without printing secrets.
7. Pushed source to GitHub.

## Commands / Validation

Backend compile:

- Command: `python -m compileall apps/backend/app -q`
- Result: PASS

Backend tests:

- Command: `.venv\Scripts\python.exe -m pytest -q`
- Result: PASS
- Evidence: `23 passed`

Frontend build:

- Command: `npm run build`
- Result: PASS
- Output: Vite production build completed

Alembic:

- Command: `.venv\Scripts\python.exe -m alembic heads`
- Result: `0002_enterprise_hardening (head)`
- Command: `.venv\Scripts\python.exe -m alembic current`
- Result: `0002_enterprise_hardening (head)`

Staging env validator:

- Command: `tools\validate_staging_config.py --mode staging`
- Result: PASS
- Checks passed:
  - Required env shape present
  - PostgreSQL URL shape
  - Database SSL enabled
  - Auto migrate explicit and false
  - Debug disabled
  - Strong generated secret shape
  - HTTPS-only CORS/frontend
  - Frontend points to HTTPS backend
  - External providers disabled

Secret scan:

- `.env` not staged.
- No real cloud secret found in committed source scan.
- Matches found were local test passwords/tokens only.

Git:

- Commit pushed: `0a0ecb5 Prepare DCFT Render staging deployment`
- Remote: `origin/main`

## Render Access Status

Render CLI:

- Not installed locally.

Render API token:

- No local environment variable found.

Render dashboard:

- Browser reached `https://dashboard.render.com/login`.
- No authenticated Render session available.

## Deployment Attempt Result

Source was pushed to GitHub, but Render did not create or deploy the expected services automatically within the validation window.

Expected URLs checked:

- `https://dcft-backend.onrender.com/health`
- `https://dcft-backend.onrender.com/runtime/status`
- `https://dcft-frontend.onrender.com`

Result:

- All remained HTTP 404 after repeated polling.

Conclusion:

- Source-to-GitHub: PASS
- Source-to-Live Render: BLOCKED
- Required missing action: authenticated Render Blueprint create/sync.
