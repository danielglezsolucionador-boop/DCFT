# DCFT Render Deploy Runbook

Estado: preparado para staging controlado. No desplegar produccion masiva desde este runbook.

Referencia Render: https://render.com/docs/blueprint-spec

## Servicios a crear

1. PostgreSQL:
   - Name: `dcft-postgres`
   - Database: `dcft`
   - User: `dcft`
   - Plan: `starter` o el plan definido por CTO antes del deploy.

2. Backend web service:
   - Name: `dcft-backend`
   - Runtime: Python
   - Health check path: `/health`
   - Build command:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - Pre-deploy command:
     ```bash
     PYTHONPATH=apps/backend alembic upgrade head
     ```
   - Start command:
     ```bash
     PYTHONPATH=apps/backend uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

3. Frontend static site:
   - Name: `dcft-frontend`
   - Root directory: `apps/frontend`
   - Build command:
     ```bash
     npm ci && npm run build
     ```
   - Publish directory:
     ```text
     dist
     ```

## Variables Render necesarias

Backend:

| Variable | Valor esperado |
| --- | --- |
| `PYTHON_VERSION` | `3.11.9` |
| `DCFT_APP_NAME` | `dcft-backend` |
| `DCFT_APP_VERSION` | Version actual del release |
| `DCFT_APP_ENV` | `staging` para staging controlado |
| `DCFT_DEBUG` | `false` |
| `DCFT_LOG_LEVEL` | `INFO` |
| `DCFT_DATABASE_URL` | Render PostgreSQL connection string |
| `DCFT_DATABASE_SSL` | `true` |
| `DCFT_DB_AUTO_MIGRATE` | `false` si se usa pre-deploy Alembic |
| `DCFT_ADMIN_USERNAME` | Usuario bootstrap administrativo |
| `DCFT_ADMIN_PASSWORD` | Secret fuerte, no commitear |
| `DCFT_JWT_SECRET` | Secret fuerte de 32+ caracteres, no commitear |
| `DCFT_JWT_PREVIOUS_SECRET` | Opcional para rotacion JWT |
| `DCFT_FRONTEND_ORIGIN` | URL HTTPS del frontend Render |
| `DCFT_CORS_ORIGINS` | URL(s) HTTPS permitidas, separadas por coma |
| `DCFT_AI_PROVIDER_ENABLED` | `false` |
| `DCFT_OCR_ENABLED` | `false` |
| `DCFT_OBSERVABILITY_PERSIST_CONCURRENCY` | `20` |

Frontend:

| Variable | Valor esperado |
| --- | --- |
| `VITE_DCFT_API_URL` | URL HTTPS del backend Render, sin slash final |

## PostgreSQL cloud

- Render debe usar PostgreSQL, nunca SQLite.
- `DCFT_DATABASE_URL` puede venir como `postgresql://...`; el backend lo normaliza a `postgresql+asyncpg://...`.
- Alembic debe correr antes del start del backend:
  ```bash
  PYTHONPATH=apps/backend alembic upgrade head
  ```
- Si Alembic falla, detener el deploy y revisar migraciones antes de iniciar trafico.

## CORS y frontend

- `VITE_DCFT_API_URL` debe apuntar al backend Render.
- `DCFT_FRONTEND_ORIGIN` debe ser la URL HTTPS exacta del frontend.
- `DCFT_CORS_ORIGINS` debe incluir la URL HTTPS exacta del frontend.
- No usar `localhost` en staging Render.

## Validacion post deploy

Backend:

```bash
curl https://BACKEND_RENDER_URL/health
curl https://BACKEND_RENDER_URL/runtime/status
```

Frontend:

1. Abrir `https://FRONTEND_RENDER_URL`.
2. Login con el usuario bootstrap configurado.
3. Verificar dashboard, runtime, auth, audit, governance y workflows basicos.
4. Revisar consola del browser sin errores CORS.

Base de datos:

1. Confirmar que Alembic dejo creada la revision `head`.
2. Confirmar tablas principales: users, tenants, audit_events, runtime_events, workflows, approval_requests, alerts.
3. Reiniciar backend y verificar que los datos persisten.

## Rollback

1. Revertir el deploy al commit anterior desde Render.
2. Si el problema es frontend, revertir solo `dcft-frontend`.
3. Si el problema es backend, revertir `dcft-backend` y conservar PostgreSQL.
4. No borrar la base hasta extraer backup.
5. Si una migracion ya corrio, validar si requiere migracion inversa manual antes de regresar codigo.

## Bloqueos de seguridad

No desplegar si ocurre cualquiera de estos casos:

- `DCFT_DATABASE_URL` esta vacio.
- `DCFT_DATABASE_URL` apunta a SQLite.
- `DCFT_DATABASE_SSL` no es `true`.
- `DCFT_DEBUG` no es `false`.
- `DCFT_ADMIN_PASSWORD` usa el default local.
- `DCFT_JWT_SECRET` usa el default local o es debil.
- `DCFT_FRONTEND_ORIGIN` o `DCFT_CORS_ORIGINS` usan `localhost`, `http://` o `*`.
- `DCFT_AI_PROVIDER_ENABLED` u `DCFT_OCR_ENABLED` se activan sin aprobacion CTO.
