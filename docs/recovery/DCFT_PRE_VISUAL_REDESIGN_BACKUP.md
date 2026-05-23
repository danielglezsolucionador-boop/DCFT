# DCFT Pre Visual Redesign Backup

Fecha de snapshot: 2026-05-23 08:31:28 -05:00

## Objetivo

Congelar el estado tecnico actual de DCFT antes de cualquier cambio de UI/UX, branding o deploy premium.

Este snapshot es solo backup y recovery. No autoriza cambios visuales, backend, auth, RBAC, multi-tenant, governance, audit, PostgreSQL, Alembic, runtime, IA u OCR.

## Identidad

- Producto: DCFT
- Nombre largo: Doctor Contable Financiero Tributario
- Tagline operativo: El medico de tu empresa

## Rutas

- Ruta local: `C:\Users\admin\dcft-knowledge-core`
- Repo: `https://github.com/danielglezsolucionador-boop/DCFT`
- Branch recovery: `dcft-pre-visual-redesign-stable`
- Tag recovery: `dcft-pre-visual-redesign-v1`
- Commit base antes del documento recovery: `34e557344c44ab498914341dd0ca0b08744903d8`

## Estructura

- `apps/backend`: backend FastAPI.
- `apps/backend/app/api`: rutas API.
- `apps/backend/app/core`: configuracion, runtime, seguridad, RBAC, observabilidad, audit.
- `apps/backend/app/db`: modelos, sesiones, repositorios, bootstrap y migraciones runtime.
- `apps/backend/alembic`: migraciones Alembic.
- `apps/backend/tests`: pruebas backend operacionales.
- `apps/frontend`: frontend React/Vite/Tailwind.
- `apps/frontend/public`: iconos, manifest PWA y favicon.
- `tools`: validadores, smoke tests y captura visual.
- `docs`: runbooks, snapshots y recovery.
- `phases`: planes por fase.
- `.dcft`: estado local ignorado por git.

## Stack

- Backend: Python, FastAPI, SQLAlchemy async, Alembic.
- Runtime local: SQLite fallback cuando `DCFT_DATABASE_URL` esta vacio.
- Runtime staging/cloud: PostgreSQL esperado con SSL.
- Frontend: React 18, Vite, TypeScript, Tailwind, lucide-react.
- Deploy configurado: Render `dcft-backend`, `dcft-frontend`, `dcft-postgres` segun `render.yaml`.
- Python version declarada: `3.11.9` en `.python-version` y Render.

## Variables Sin Valores Secretos

Variables backend conocidas:

- `PYTHON_VERSION`
- `DCFT_APP_NAME`
- `DCFT_APP_VERSION`
- `DCFT_APP_ENV`
- `DCFT_DEBUG`
- `DCFT_LOG_LEVEL`
- `DCFT_DATABASE_URL`
- `DCFT_DATABASE_SSL`
- `DCFT_DB_AUTO_MIGRATE`
- `DCFT_ADMIN_USERNAME`
- `DCFT_ADMIN_PASSWORD`
- `DCFT_JWT_SECRET`
- `DCFT_JWT_ALGORITHM`
- `DCFT_JWT_EXP_MINUTES`
- `DCFT_FRONTEND_ORIGIN`
- `DCFT_CORS_ORIGINS`
- `DCFT_AI_PROVIDER_ENABLED`
- `DCFT_OCR_ENABLED`
- `DCFT_OBSERVABILITY_PERSIST_CONCURRENCY`

Variables frontend conocidas:

- `VITE_DCFT_API_URL`

Regla: no commitear `.env`, `.env.local`, secretos, tokens, dumps con credenciales ni directorios `.dcft` completos.

## Estado Backend

- App FastAPI: `apps/backend/app/main.py`.
- Health route estable: `/health`.
- Runtime route estable: `/runtime/status`.
- Alembic head: `0002_enterprise_hardening`.
- AI provider: deshabilitado por defecto.
- OCR: deshabilitado por defecto.
- Runtime safety: configurado en `apps/backend/app/core/config.py`.

## Estado Frontend

- App React/Vite: `apps/frontend/src/App.tsx`.
- API client: `apps/frontend/src/lib/api.ts`.
- Build output: `apps/frontend/dist` generado solo como artefacto local ignorado.
- PWA assets existentes: `manifest.webmanifest`, `icon-192.png`, `icon-512.png`, `apple-touch-icon.png`, `favicon.ico`.

## Validaciones Ejecutadas

- `pytest -q` con `.venv\Scripts` al frente del `PATH`: OK, 14 passed.
- `.venv\Scripts\python.exe -m pytest -q`: OK, 14 passed.
- `npm run build` en `apps/frontend`: OK.
- `.venv\Scripts\python.exe -m compileall apps/backend/app tools -q`: OK.
- `.venv\Scripts\python.exe -m alembic heads`: OK, `0002_enterprise_hardening (head)`.
- `.venv\Scripts\python.exe -m alembic current`: OK, `0002_enterprise_hardening (head)`.
- Smoke local `http://127.0.0.1:8198/health`: OK, HTTP 200.
- Smoke local `http://127.0.0.1:8198/runtime/status`: OK, HTTP 200.

Nota: las URLs cloud inferidas `https://dcft-backend.onrender.com` y `https://dcft-frontend.onrender.com` devolvieron 404 durante esta fase, por lo que no se consideran cloud disponible para este snapshot.

## Backups

Destino local: `C:\Users\admin\dcft-backups`

Archivos esperados:

- `dcft-pre-visual-redesign-source-no-secrets-20260523-083128.zip`
- `dcft-pre-visual-redesign-state-20260523-083128.zip`

El ZIP de codigo excluye:

- `.git`
- `.env`
- `.env.local`
- `.dcft`
- `.venv`
- `node_modules`
- `dist`
- `.pytest_cache`
- `__pycache__`
- `*.pyc`
- `*.log`
- `*.tsbuildinfo`

El ZIP de estado local incluye solo artefactos controlados de `.dcft`:

- JSON/JSONL de estado y audit.
- SQLite local `dcft_local.db` si existe.
- screenshots PNG existentes.
- outputs/uploads controlados.

El ZIP de estado excluye perfiles de navegador `chrome-*`, logs y caches para evitar datos sensibles o ruido operativo.

## Rollback

Rollback rapido a este snapshot:

```powershell
cd C:\Users\admin\dcft-knowledge-core
git fetch origin --tags
git switch dcft-pre-visual-redesign-stable
git reset --hard dcft-pre-visual-redesign-v1
```

Restaurar desde ZIP de codigo:

```powershell
Expand-Archive -Path C:\Users\admin\dcft-backups\dcft-pre-visual-redesign-source-no-secrets-20260523-083128.zip -DestinationPath C:\Users\admin\dcft-restore -Force
```

Restaurar estado local controlado:

```powershell
Expand-Archive -Path C:\Users\admin\dcft-backups\dcft-pre-visual-redesign-state-20260523-083128.zip -DestinationPath C:\Users\admin\dcft-restore-state -Force
```

## Que No Tocar En Esta Fase

- UI/UX.
- Branding.
- Backend.
- Auth.
- RBAC.
- Multi-tenant.
- Governance.
- Audit.
- PostgreSQL.
- Alembic.
- Runtime.
- Render/deploy.
- IA.
- OCR.
- Secrets.
- Refactors.

## Estado Final

Este recovery documenta el estado previo al rediseño premium. Nuevos cambios visuales deben salir despues de este branch/tag y con validacion visual separada.
