# DCFT Postgres Production Persistence Report

Fecha: 2026-06-03

## Ejecucion final 2026-06-04

Contexto recibido:

- Neon ya fue creado y conectado al proyecto Vercel backend `dcft`.
- No se creo otra base.
- No se conecto `dcft-frontend`.
- No se toco FORJA.
- No se toco CEREBRO.
- No se rediseno UI.
- No se implemento SUNAT real.

### Variables Vercel Production verificadas

Proyecto backend: `dcft`

Variables verificadas sin imprimir valores:

- `DATABASE_URL`: presente, no vacia.
- `DATABASE_URL_UNPOOLED`: presente, no vacia.
- `PGHOST`: presente, no vacia.
- `PGUSER`: presente, no vacia.
- `PGPASSWORD`: presente, no vacia.
- `PGDATABASE`: presente, no vacia.
- `POSTGRES_URL`: presente, no vacia.
- `POSTGRES_PRISMA_URL`: presente, no vacia.

Hallazgo:

- El recurso Neon `neon-cerulean-bridge` estaba conectado, pero las variables estaban vacias al hacer pull.
- Se desconecto y reconecto el mismo recurso al proyecto `dcft`.
- Despues de reconectar, las variables quedaron no vacias.
- No se creo una base nueva.

### Compatibilidad Neon / asyncpg

Neon entrego una URL con query params:

- `sslmode=require`
- `channel_binding=require`

`asyncpg` no acepta esos parametros como kwargs directos.

Correccion aplicada:

- Normalizar URLs `postgres://` / `postgresql://` a `postgresql+asyncpg://`.
- Remover `sslmode` de la URL SQLAlchemy y traducirlo a `connect_args["ssl"] = True`.
- Remover `channel_binding` para evitar:

```text
TypeError: connect() got an unexpected keyword argument 'channel_binding'
```

Archivos:

- `apps/backend/app/core/config.py`
- `apps/backend/tests/test_operational_backend.py`

### Migraciones Alembic contra Neon

Ejecucion:

- Se cargo Production env desde Vercel sin imprimir secretos.
- Se uso `DATABASE_URL_UNPOOLED` como `DCFT_DATABASE_URL` para migraciones.
- Se ejecuto:

```powershell
python -m alembic upgrade head
```

Resultado:

- PASS
- Dialecto: `PostgresqlImpl`
- Migraciones ejecutadas:
  - `0001_dcft_foundation`
  - `0002_enterprise_hardening`
  - `0003_heart_a1_domain_identity`
  - `0004_heart_a1_user_plans`
  - `0005_heart_a2_sunat`
  - `0006_auth_trial_onboarding`

### Produccion backend validada

URL:

- `https://dcft.vercel.app/health`
- `https://dcft.vercel.app/runtime/status`

Resultado:

```json
{
  "environment": "production",
  "production_ready": true,
  "database": {
    "backend": "postgresql",
    "persistent": true,
    "temporal": false,
    "source": "DATABASE_URL",
    "postgres": true,
    "sqlite": false,
    "status": "ok",
    "reason": "connection_ok"
  },
  "security_warnings": []
}
```

### Validacion funcional real en produccion

Usuarios de prueba creados en Postgres:

- Estudiante: `student_pg_20260604074614`
- MYPE: `mype_pg_20260604074614`

Resultados:

- Registro estudiante: PASS.
- Login estudiante: PASS.
- Estudiante sin RUC: PASS.
- Trial estudiante: `active`, vence `2026-06-11T12:46:15.362903+00:00`.
- MYPE sin RUC: PASS, devuelve 422 con `ruc_required_for_business_plan`.
- MYPE con RUC: PASS.
- Empresa creada: PASS, RUC `20260604074`.
- Workspace creado: PASS, `workspace-07d6251d45ac49e1949facde8ba1a9a9`.
- Contexto activo con empresa/workspace: PASS.
- Trial MYPE: `active`, vence `2026-06-11T12:46:19.673115+00:00`.
- Logout/login posterior: PASS.

### Persistencia post-redeploy

Se ejecuto redeploy backend despues de crear usuarios/datos.

Despues del redeploy:

- Login estudiante existente: PASS.
- Trial estudiante persistido: PASS.
- Login MYPE existente: PASS.
- Trial MYPE persistido: PASS.
- Empresa MYPE persistida: PASS.
- Workspace MYPE persistido: PASS.
- Contexto workspace persistido: PASS.

### Frontend y seguridad

Frontend:

- `https://dcft-frontend.vercel.app`: PASS.
- Mobile 390x844: PASS.
- Desktop 1440x1000: PASS.
- Overflow horizontal: NO.
- Console errors: 0.
- `Backend API URL is not configured`: NO.
- `Runtime degradado`: NO.

Seguridad:

- `DATABASE_URL` no aparece en HTML publico.
- URLs Postgres no aparecen en HTML publico.
- `PGPASSWORD` no aparece en HTML publico.
- `DCFT_JWT_SECRET` no aparece en HTML publico.
- `DCFT_ADMIN_PASSWORD` no aparece en HTML publico.
- Secret scan repo: sin secretos reales; solo URLs ficticias `user:pass@db.example.com` en tests.
- Archivo temporal de env eliminado.
- `.env` no fue commiteado.

### Validaciones locales

- `python -m compileall apps/backend/app tools -q`: PASS.
- `pytest apps/backend/tests -q`: PASS, 29 passed.
- `npm run build`: PASS.

### Estado final 2026-06-04

- Postgres persistent PASS: SI.
- SQLite temporal OFF: SI.
- Migraciones PASS: SI.
- Usuario persiste PASS: SI.
- Workspace persiste PASS: SI.
- Trial persiste PASS: SI.
- Redeploy conserva datos PASS: SI.
- Backend production PASS: SI.
- Frontend production PASS: SI.
- Secrets expuestos: NO.
- DCFT listo para pruebas controladas con usuarios reales: SI.

## Ejecucion actual 2026-06-03 23:42

Backup nuevo creado antes de cualquier intento:

- Ruta: `D:\ECOSYSTEM\BACKUPS\dcft-postgres-prechange-20260603-234202.zip`
- Tamano: 37.69 MB
- Fecha: 2026-06-03 23:42:11
- Archivos incluidos: 2950
- Estado Git al iniciar: limpio en `main`
- Commit inicial: `bea1497 docs: record dcft postgres persistence blocker`

Estado productivo verificado:

- Backend project Vercel: `dcft`
- Frontend project Vercel: `dcft-frontend`
- `https://dcft.vercel.app/health`: 200
- `database.backend=sqlite`
- `database.persistent=false`
- `database.temporal=true`
- `database.source=missing`
- `database.postgres=false`
- `database.sqlite=true`

Intento de provision Neon Free:

```powershell
npx vercel integration add neon --plan free_v3 --name dcft-postgres --metadata region=iad1 --metadata auth=false --environment production --no-env-pull --format=json
```

Resultado:

```text
status=action_required
reason=integration_terms_acceptance_required
```

Bloqueo actual:

```text
Aceptacion humana obligatoria de terminos Neon Marketplace.
```

URL exacta:

```text
https://vercel.com/danielglezsolucionador-boops-projects/~/integrations/accept-terms/neon?source=cli
```

No se puede completar Postgres persistente real hasta aceptar esos terminos en Vercel.

## 1. Backup creado

- Ruta: `D:\ECOSYSTEM\BACKUPS\dcft-postgres-prechange-20260603-225915.zip`
- Tamano: 37.69 MB
- Fecha: 2026-06-03 22:59:24
- Archivos incluidos: 2949
- Estado: OK
- Exclusiones: `.git`, `node_modules`, `build`, `dist`, `__pycache__`, `.pytest_cache`, `.venv`, `venv`, `.vercel`, `.env`, `.env.*`, logs, archivos con nombre `secret`/`secrets`.

## 2. Estado de repositorio

- Repo local: `C:\Users\admin\dcft-knowledge-core`
- Branch: `main`
- Remote: `https://github.com/danielglezsolucionador-boop/DCFT.git`
- Commit base al iniciar: `4e93ffc docs: record dcft auth roles trial onboarding validation`
- Estado inicial Git: limpio.

## 3. Stack DB detectado

- Backend: FastAPI.
- ORM: SQLAlchemy async.
- Driver Postgres: `asyncpg`.
- Driver SQLite local: `aiosqlite`.
- Migraciones: Alembic.
- Modelos: `apps/backend/app/db/models.py`.
- Base declarativa: `apps/backend/app/db/base.py`.
- Sesion DB: `apps/backend/app/db/session.py`.
- Configuracion DB: `apps/backend/app/core/config.py`.
- Migraciones: `apps/backend/alembic/versions/`.
- Alembic config: `alembic.ini`.

## 4. Estado anterior SQLite temporal

Produccion actual antes de Postgres:

- Backend: `https://dcft.vercel.app`
- Frontend: `https://dcft-frontend.vercel.app`
- `/health`: 200
- `/runtime/status`: 200
- `environment=local`
- `database.backend=sqlite`
- `production_ready=false`
- Warning: `sqlite_local_fallback_active`

Conclusion: DCFT esta accesible, pero NO esta listo para usuarios reales porque la DB productiva no es persistente.

Despues del commit `2a18ff6`, el alias publico ya expone indicadores seguros adicionales:

```json
{
  "database": {
    "backend": "sqlite",
    "persistent": false,
    "temporal": true,
    "source": "missing",
    "postgres": false,
    "sqlite": true,
    "status": "ok"
  },
  "security_warnings": [
    "sqlite_local_fallback_active",
    "vercel_production_app_env_local",
    "vercel_production_requires_postgresql"
  ]
}
```

Esto no resuelve Postgres, pero elimina la ambiguedad: produccion informa claramente que esta temporal y bloqueada.

## 5. Por que cae a SQLite

`Settings.effective_database_url` usaba `DCFT_DATABASE_URL`.

Si `DCFT_DATABASE_URL` estaba vacio, el backend caia a:

```text
sqlite+aiosqlite:///<base_dir>/.dcft/state/dcft_local.db
```

En Vercel, `DCFT_BASE_DIR=/tmp/dcft`, por lo que la base queda en almacenamiento temporal.

Variables productivas detectadas en Vercel backend:

- `DCFT_ADMIN_PASSWORD`
- `DCFT_ADMIN_USERNAME`
- `DCFT_AI_PROVIDER_ENABLED`
- `DCFT_APP_ENV`
- `DCFT_BASE_DIR`
- `DCFT_CORS_ORIGINS`
- `DCFT_DB_AUTO_MIGRATE`
- `DCFT_DEBUG`
- `DCFT_FRONTEND_ORIGIN`
- `DCFT_JWT_SECRET`
- `DCFT_OCR_ENABLED`

Variables DB ausentes:

- `DCFT_DATABASE_URL`
- `DATABASE_URL`

## 6. Cambios implementados

### Soporte de `DATABASE_URL`

Archivo: `apps/backend/app/core/config.py`

DCFT ahora acepta:

1. `DCFT_DATABASE_URL`
2. `DATABASE_URL`

Orden de prioridad:

```text
DCFT_DATABASE_URL -> DATABASE_URL -> SQLite local
```

Esto permite conectar proveedores Vercel Marketplace que entregan `DATABASE_URL` sin duplicar secretos.

### Indicadores seguros de persistencia

Archivo: `apps/backend/app/db/session.py`

`/health` y `/runtime/status` ahora pueden devolver, sin exponer secretos:

```json
{
  "backend": "postgresql|sqlite",
  "persistent": true,
  "temporal": false,
  "source": "DCFT_DATABASE_URL|DATABASE_URL|missing",
  "postgres": true,
  "sqlite": false
}
```

### Warnings de Vercel produccion

Archivo: `apps/backend/app/core/config.py`

Si Vercel esta en `VERCEL_ENV=production` y el backend sigue local/SQLite, se agregan warnings:

- `vercel_production_app_env_local`
- `vercel_production_requires_postgresql`

## 7. Proveedor Postgres

No se pudo crear Postgres real todavia porque Vercel exige aceptacion humana de terminos del Marketplace.

Intentos ejecutados:

### Neon Free

Comando:

```powershell
npx vercel integration add neon --plan free_v3 --name dcft-postgres --metadata region=iad1 --metadata auth=false --environment production --no-env-pull --format=json
```

Resultado:

```text
action_required
integration_terms_acceptance_required
```

URL para aceptar:

```text
https://vercel.com/danielglezsolucionador-boops-projects/~/integrations/accept-terms/neon?source=cli
```

### Prisma Postgres Free

Comando:

```powershell
npx vercel integration add prisma/prisma-postgres --plan free --name dcft-postgres --metadata region=iad1 --environment production --no-env-pull --format=json
```

Resultado:

```text
action_required
integration_terms_acceptance_required
```

URL para aceptar:

```text
https://vercel.com/danielglezsolucionador-boops-projects/~/integrations/accept-terms/prisma?source=cli
```

Recomendacion: usar Neon Free para DCFT porque es Postgres directo y compatible con `asyncpg`.

## 8. Variables que deben quedar en Vercel backend

Requeridas para cerrar produccion real:

```text
DATABASE_URL=<provista por Neon/Vercel Marketplace>
DCFT_APP_ENV=production
DCFT_DATABASE_SSL=true
DCFT_DB_AUTO_MIGRATE=false
DCFT_DEBUG=false
DCFT_FRONTEND_ORIGIN=https://dcft-frontend.vercel.app
DCFT_CORS_ORIGINS=https://dcft-frontend.vercel.app,https://dcft-frontend-danielglezsolucionador-boops-projects.vercel.app
DCFT_AI_PROVIDER_ENABLED=false
DCFT_OCR_ENABLED=false
```

Ya existen y no deben imprimirse:

```text
DCFT_JWT_SECRET
DCFT_ADMIN_PASSWORD
```

## 9. Migraciones

Migraciones disponibles:

- `0001_dcft_foundation`
- `0002_enterprise_hardening`
- `0003_heart_a1_domain_identity`
- `0004_heart_a1_user_plan_assignments`
- `0005_heart_a2_sunat_foundation`
- `0006_auth_trial_onboarding`

Migracion contra Postgres real:

- Estado: NO EJECUTADA.
- Motivo: no existe todavia `DATABASE_URL` productiva.

Comando recomendado despues de aceptar Neon y crear recurso:

```powershell
npx vercel env run -- powershell -NoProfile -Command "$env:PYTHONPATH='apps/backend'; .\.venv\Scripts\python.exe -m alembic upgrade head"
```

No ejecutar `db push`.
No resetear DB.
No borrar tablas.

## 10. Validacion de usuario/empresa/workspace/trial

Validacion real contra Postgres:

- Estado: NO EJECUTADA.
- Motivo: Postgres cloud aun no existe/conectado.

Validacion previa contra produccion temporal ya existia, pero no sirve como certificacion productiva persistente.

Prueba obligatoria posterior a Postgres:

1. Crear usuario Estudiante.
2. Login Estudiante.
3. Confirmar sin RUC.
4. Crear MYPE sin RUC.
5. Confirmar 422.
6. Crear MYPE con RUC.
7. Confirmar empresa.
8. Confirmar workspace.
9. Confirmar trial 7 dias.
10. Logout.
11. Login posterior.
12. Confirmar persistencia despues de recarga/cold start.

## 11. Frontend

Frontend actual:

- `https://dcft-frontend.vercel.app`: PASS previo.
- No se modifico UI.
- No se redisenio.
- No se implemento SUNAT real.

Frontend debe revalidarse despues de migrar a Postgres.

## 12. Backend

Backend actual:

- `/health`: 200
- `/runtime/status`: 200
- DB actual: SQLite temporal
- Produccion real: NO

Backend preparado para aceptar `DATABASE_URL`: SI

## 13. Seguridad / secrets

Secret scan:

- No se detectaron secretos reales.
- Hallazgos fueron nombres de variables y URLs ficticias de tests `user:pass@db.example.com`.
- No se imprimio `DATABASE_URL` real.
- No se hizo pull persistente de variables secretas.
- El archivo temporal de auditoria de env fue eliminado.

## 14. Validaciones ejecutadas

- `python -m compileall apps/backend/app tools -q`: PASS
- `pytest apps/backend/tests -q`: PASS, 28 passed
- `npm run build`: PASS
- Secret scan basico: PASS con observacion de ejemplos ficticios.
- Deploy automatico Vercel del commit `2a18ff6`: READY
- `https://dcft.vercel.app/health`: PASS, con `database.persistent=false`, `database.temporal=true`, `database.source=missing`
- `https://dcft.vercel.app/runtime/status`: PASS, con `database.postgres=false`, `database.sqlite=true`

## 15. Archivos modificados

- `apps/backend/app/core/config.py`
- `apps/backend/app/db/session.py`
- `apps/backend/tests/test_operational_backend.py`
- `DCFT_POSTGRES_PRODUCTION_PERSISTENCE_REPORT.md`

## 16. Que NO se toco

- No se toco FORJA.
- No se toco CEREBRO.
- No se toco CENTINELA.
- No se redisenio UI.
- No se cambio login/roles/trial/onboarding funcional.
- No se implemento SUNAT real.
- No se expusieron secrets.
- No se borro data.
- No se reseteo ninguna DB.

## 17. Pendientes reales

Bloqueo humano externo:

1. Aceptar terminos de Neon Marketplace:

```text
https://vercel.com/danielglezsolucionador-boops-projects/~/integrations/accept-terms/neon?source=cli
```

2. Reintentar provision:

```powershell
npx vercel integration add neon --plan free_v3 --name dcft-postgres --metadata region=iad1 --metadata auth=false --environment production --no-env-pull --format=json
```

3. Confirmar que Vercel inyecta `DATABASE_URL`.

4. Cambiar backend a produccion real:

```powershell
vercel env update DCFT_APP_ENV production
vercel env update DCFT_DATABASE_SSL production
vercel env update DCFT_DB_AUTO_MIGRATE production
```

Valores:

```text
DCFT_APP_ENV=production
DCFT_DATABASE_SSL=true
DCFT_DB_AUTO_MIGRATE=false
```

5. Ejecutar Alembic contra Postgres:

```powershell
npx vercel env run -- powershell -NoProfile -Command "$env:PYTHONPATH='apps/backend'; .\.venv\Scripts\python.exe -m alembic upgrade head"
```

6. Redeploy backend:

```powershell
npx vercel deploy . --project dcft --prod --yes
```

7. Validar:

```text
https://dcft.vercel.app/health
https://dcft.vercel.app/runtime/status
```

Criterios:

- `database.backend=postgresql`
- `database.persistent=true`
- `database.temporal=false`
- `database.sqlite=false`
- `database.postgres=true`
- `production_ready=true`

## 18. Estado final de esta ejecucion

- Backup creado: SI
- Stack DB detectado: SI
- Soporte `DATABASE_URL`: SI
- Indicadores persistencia/temporal: SI
- Indicadores desplegados en produccion: SI
- Tests PASS: SI
- Build PASS: SI
- Secret scan PASS: SI
- Postgres cloud creado: NO
- Motivo: aceptacion humana de terminos Marketplace requerida.
- Migraciones Postgres ejecutadas: NO
- Persistencia productiva validada: NO
- DCFT listo para usuarios reales: NO
