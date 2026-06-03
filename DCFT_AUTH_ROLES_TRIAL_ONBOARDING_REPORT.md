# DCFT Auth, Roles, Trial y Onboarding Report

Fecha: 2026-06-03

## Objetivo

Resolver la base operativa de DCFT antes de cualquier redisenio visual:

- Produccion accesible.
- Login y registro visibles.
- Roles y planes base operativos.
- Trial Premium de 7 dias preparado.
- Onboarding seguro.
- SUNAT preparado solo como foundation segura con usuario secundario/auxiliar.
- Sin integracion SUNAT real.
- Sin tocar FORJA ni CEREBRO.

## Backup pre-cambio

- Ruta: `D:\ECOSYSTEM\BACKUPS\dcft-auth-onboarding-prechange-20260603-101431.zip`
- Tamano: 37.76 MB
- Fecha: 2026-06-03 10:15:56
- Estado: OK
- Exclusiones aplicadas: `.git`, `node_modules`, `build`, `dist`, `__pycache__`, `.pytest_cache`, `.venv`, `venv`, `.env`, logs, archivos de secrets.

## Diagnostico de produccion inicial

- `https://dcft.vercel.app`: 404 / deployment no funcional.
- `https://dcft-frontend.vercel.app`: frontend servia version antigua/demo.
- Problema visible: `Backend API URL is not configured. Runtime degradado.`
- Causa frontend: falta de `VITE_DCFT_API_URL` en Vercel.
- Causa backend inicial: Vercel no estaba sirviendo correctamente FastAPI y posteriormente cargaba `.env` local con `127.0.0.1:5432`.

## Cambios implementados

### Backend

- Normalizacion de planes:
  - `student` / Estudiante.
  - `mype` / MYPE.
  - `premium` / Premium.
- Compatibilidad con aliases heredados:
  - `free_student`.
  - `business_basic`.
  - `business_premium`.
- Onboarding seguro:
  - Estudiante no requiere RUC y no crea empresa.
  - MYPE requiere RUC.
  - Premium requiere RUC.
  - Trial activo de 7 dias cuando aplica.
  - Creacion atomica de tenant, usuario admin, subscripcion, empresa, workspace, membership y contexto activo cuando corresponde.
- SUNAT foundation:
  - Solo preparacion para usuario secundario/auxiliar.
  - Sin conexion real.
  - Sin presentar declaraciones.
  - Sin firmar documentos.
  - Sin acciones tributarias.
- Configuracion Vercel backend:
  - `api/index.py`.
  - `vercel.json`.
  - `.python-version` ajustado a `3.12`.
  - `.vercelignore` para impedir subida de `.env` y artefactos locales.

### Frontend

- Registro visible desde login.
- Selector de tipo de cuenta:
  - Estudiante.
  - Empresa.
- Planes visibles:
  - Estudiante.
  - MYPE.
  - Premium.
- Trial visible.
- Campos RUC/razon social solo para empresa.
- Mensaje seguro de SUNAT auxiliar/secundario.
- Slots para guias de video.
- Correccion mobile para evitar overflow horizontal.
- Configuracion Vercel frontend:
  - `apps/frontend/vercel.json` con `outputDirectory: dist`.

## Variables configuradas / validadas

### Backend Vercel

- `DCFT_APP_ENV=local`
- `DCFT_DEBUG=false`
- `DCFT_BASE_DIR=/tmp/dcft`
- `DCFT_DB_AUTO_MIGRATE=true`
- `DCFT_ADMIN_USERNAME=dcft_admin`
- `DCFT_FRONTEND_ORIGIN=https://dcft-frontend.vercel.app`
- `DCFT_CORS_ORIGINS=https://dcft-frontend.vercel.app,https://dcft-frontend-danielglezsolucionador-boops-projects.vercel.app`
- `DCFT_AI_PROVIDER_ENABLED=false`
- `DCFT_OCR_ENABLED=false`
- `DCFT_JWT_SECRET` configurado con valor generado, no impreso en el reporte.
- `DCFT_ADMIN_PASSWORD` configurado con valor generado, no impreso en el reporte.

### Frontend Vercel

- `VITE_DCFT_API_URL=https://dcft.vercel.app`

## Deploys realizados

Commits:

- `7bc912d implement dcft auth roles trial and onboarding foundation`
- `d8bd081 fix dcft vercel python runtime`
- `4547421 fix dcft vercel deployment ignores`
- `5ed3882 fix dcft frontend vercel output`

Produccion:

- Backend: `https://dcft.vercel.app`
- Frontend: `https://dcft-frontend.vercel.app`
- Frontend deployment: `https://dcft-frontend-moml6bu3a-danielglezsolucionador-boops-projects.vercel.app`

## Validaciones locales

- `python -m compileall apps/backend/app tools -q`: PASS
- `pytest apps/backend/tests -q`: PASS, 26 passed
- `npm run build`: PASS
- Backend startup local: PASS
- `/health` local: PASS
- `/runtime/status` local: PASS
- Onboarding Estudiante sin RUC: PASS
- MYPE sin RUC bloqueado con 422: PASS
- MYPE con RUC crea empresa/workspace/contexto: PASS
- Login posterior al onboarding: PASS
- Mobile local sin overflow: PASS

## Validaciones productivas

### Frontend

- `https://dcft-frontend.vercel.app`: 200
- Root SPA presente: SI
- Assets servidos: SI
- `DEPLOYMENT_NOT_FOUND`: NO
- `Backend API URL is not configured`: NO
- `Runtime degradado`: NO

### Backend

- `https://dcft.vercel.app/health`: 200
- `https://dcft.vercel.app/runtime/status`: 200
- `https://dcft.vercel.app/onboarding/status`: 200
- Planes Estudiante/MYPE/Premium presentes: SI
- SUNAT auxiliar/secundario documentado en onboarding: SI

### Flujo productivo

- Estudiante sin RUC:
  - Plan: `student`
  - Nombre: `Estudiante`
  - Trial: `active`
  - Dias: 7
  - Empresa creada: NO
  - Token devuelto: SI
- MYPE sin RUC:
  - Status: 422
  - Error: `ruc_required_for_business_plan`
- MYPE con RUC:
  - Empresa creada: SI
  - Workspace creado: SI
  - Login posterior: PASS

### Navegador productivo

Mobile 390x844:

- DCFT visible: SI
- Crear cuenta visible: SI
- Estudiante visible: SI
- MYPE visible: SI
- Premium visible: SI
- Trial visible: SI
- SUNAT auxiliar visible: SI
- Overflow horizontal: NO
- Console errors: 0

Desktop 1440x1000:

- DCFT visible: SI
- Crear cuenta visible: SI
- Estudiante visible: SI
- MYPE visible: SI
- Premium visible: SI
- Trial visible: SI
- SUNAT auxiliar visible: SI
- Overflow horizontal: NO
- Console errors: 0

## Secret scan

Resultado: PASS con observacion.

No se detectaron claves reales expuestas. El scan encontro solamente:

- Nombres de variables de entorno en codigo/herramientas.
- Ejemplos ficticios de tests como `user:pass@db.example.com`.
- Referencias documentales a `DCFT_DATABASE_URL`.

No se imprimieron secretos reales en este reporte.

## Estado real actual

### Resuelto

- Produccion frontend ya no devuelve 404.
- Produccion backend ya no devuelve 404.
- Frontend ya no queda degradado por API URL ausente.
- Login esta disponible.
- Registro esta disponible.
- Roles/planes base estan disponibles.
- Trial de 7 dias esta operativo.
- Onboarding diferencia Estudiante vs Empresa.
- Estudiante no requiere RUC.
- MYPE/Premium requieren RUC.
- SUNAT queda preparado solo como foundation segura con usuario auxiliar/secundario.
- Mobile 390x844 PASS.
- Desktop PASS.

### Bloqueo restante

El backend productivo esta operativo usando SQLite temporal en Vercel:

- `database.backend=sqlite`
- `environment=local`
- `production_ready=false`
- Warning: `sqlite_local_fallback_active`

Esto permite validar el flujo, pero NO es persistencia cloud definitiva. Para produccion real persistente falta configurar `DATABASE_URL` con Postgres cloud y ejecutar migraciones contra esa base.

## Resultado

- Produccion accesible: SI
- Login visible y funcional: SI
- Registro visible y funcional: SI
- Roles/planes base: SI
- Trial 7 dias: SI
- Onboarding operativo: SI
- SUNAT real implementado: NO, por restriccion de seguridad y alcance.
- SUNAT auxiliar foundation: SI
- Mobile PASS: SI
- Desktop PASS: SI
- Secret exposure: NO
- Persistencia cloud definitiva: NO

## Siguiente paso recomendado

Cerrar persistencia productiva con Postgres cloud:

1. Crear o seleccionar base Postgres para DCFT.
2. Configurar `DCFT_DATABASE_URL` o `DATABASE_URL` en Vercel.
3. Mantener `DCFT_DB_AUTO_MIGRATE=true` durante el primer deploy de migracion.
4. Redeploy backend.
5. Validar `/health` y `/runtime/status` con `database.backend=postgres`.
6. Repetir onboarding/login y confirmar persistencia post-cold-start.
