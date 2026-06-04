# DCFT Admin Trial Onboarding SUNAT Aux Report

## Backup

- Backup pre-cambio: `D:\ECOSYSTEM\BACKUPS\dcft-admin-onboarding-prechange-20260604-091957.zip`
- Repo local: `C:\Users\admin\dcft-knowledge-core`
- Branch inicial: `main`
- Commit base observado: `f9e61c4 complete dcft postgres production persistence`

## Implementado

- Admin CEO minimo protegido por backend en `/admin/ceo/users`.
- Activacion/desactivacion manual de Premium trial 7 dias por usuario.
- Cambio manual de plan por Admin CEO.
- Calculo de `plan_effective`: Premium durante trial activo; plan base al vencer o desactivar.
- Limites backend usan `plan_effective` durante trial activo y conservan el plan base.
- Tabla persistente `onboarding_progress`.
- Endpoint `GET /onboarding/progress`.
- Endpoint `POST /onboarding/videos/{video_id}/seen`.
- Tres slots de video de onboarding.
- Checklist persistente de onboarding.
- Flujo SUNAT auxiliar preparado en `/sunat/auxiliary-access/prepare`.
- UI segura para SUNAT auxiliar sin pedir Clave SOL principal ni password.

## Seguridad

- Admin CEO requiere `super_admin` o el usuario configurado por `DCFT_ADMIN_USERNAME`.
- Usuarios normales reciben 403 en endpoints admin.
- Trial no puede activarse desde endpoint publico de usuario.
- SUNAT auxiliar usa `extra=forbid`; campos como `password` son rechazados con 422.
- No se almacena password SUNAT.
- No se imprime `DATABASE_URL`.
- No se modifico `.env`.

## Validaciones

- `python -m compileall apps\backend\app tools -q`: PASS.
- `.venv\Scripts\python.exe -m pytest apps\backend\tests -q`: PASS, 32 passed.
- Migracion local temporal SQLite a head: PASS.
- `npm run build`: PASS.
- Smoke local `/health`: 200 OK.
- Smoke local `/runtime/status`: 200 OK.
- Browser local mobile-width: backend conectado, overflow horizontal NO, console errors 0.
- Servidores locales de prueba cerrados al finalizar.

## Archivos Modificados

- `apps/backend/app/db/models.py`
- `apps/backend/app/db/repositories.py`
- `apps/backend/app/schemas/common.py`
- `apps/backend/app/services/admin_service.py`
- `apps/backend/app/services/onboarding_service.py`
- `apps/backend/app/services/sunat_service.py`
- `apps/backend/app/services/subscription_service.py`
- `apps/backend/app/api/admin.py`
- `apps/backend/app/api/onboarding.py`
- `apps/backend/app/api/sunat.py`
- `apps/backend/app/main.py`
- `apps/backend/app/services/dashboard_service.py`
- `apps/backend/alembic/versions/0007_admin_onboarding_sunat_aux.py`
- `apps/backend/tests/test_operational_backend.py`
- `apps/frontend/src/App.tsx`
- `apps/frontend/src/styles.css`
- `DCFT_ONBOARDING_VIDEO_SCRIPTS.md`
- `DCFT_USER_TESTING_CHECKLIST.md`
- `DCFT_ADMIN_TRIAL_ONBOARDING_SUNAT_AUX_REPORT.md`

## No Implementado

- No se implemento scraping SUNAT.
- No se implemento conector SUNAT real.
- No se pidio Clave SOL principal.
- No se guardaron credenciales SUNAT.
- No se redisenaron pantallas.
- No se tocaron FORJA, CEREBRO ni otros proyectos.

## Pendientes Reales

- Validar en produccion tras deploy.
- Confirmar credenciales/usuario Admin CEO productivo.
- Ejecutar prueba manual con testers reales.
- Definir vault/encriptacion antes de cualquier password SUNAT futuro.
