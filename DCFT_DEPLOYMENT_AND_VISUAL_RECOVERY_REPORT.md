# DCFT Deployment and Visual Recovery Report

Fecha: 2026-06-03 08:15 America/Lima

## Resultado ejecutivo

La causa principal de que produccion no mostrara la visual oficial era source-to-live incompleto:

- El commit visual oficial `e8bbc91 upgrade dcft visual identity mobile first` existia localmente.
- GitHub `origin/main` seguia en `aa5fb6d`.
- Vercel solo podia construir desde GitHub, por lo tanto seguia sirviendo un bundle anterior.

La visual oficial ya fue aplicada en produccion mediante push de `e8bbc91` a `origin/main`.

El frontend sigue mostrando runtime degradado por una segunda causa independiente:

- El build productivo de Vercel no tiene inyectada `VITE_DCFT_API_URL`.
- El codigo frontend muestra `Backend API URL is not configured` cuando esa variable no existe en produccion.
- El backend esperado `https://dcft-backend.onrender.com/health` devuelve 404, por lo que no hay backend live validado para conectar todavia.

## Backup previo

Backup creado antes de cualquier cambio:

`D:\ECOSYSTEM\BACKUPS\dcft-production-visual-recovery-20260603-080649.zip`

Tamanio: 38.11 MB

Exclusiones aplicadas:

- `.git`
- `node_modules`
- `build`
- `dist`
- `__pycache__`
- `.venv`
- `venv`
- `.env`
- `.env.*`
- archivos `*.log`
- rutas con `secret` o `secrets`

## Evidencia Git

Repositorio:

`https://github.com/danielglezsolucionador-boop/DCFT.git`

Estado antes del push:

- `HEAD`: `e8bbc91cdf4b3f599f2893a6013d9d1f0e156b7b`
- `origin/main`: `aa5fb6d4eb996d015afeb5da67bfdf84944a0863`
- Estado: `main...origin/main [ahead 1]`

Commit visual local:

`e8bbc91 upgrade dcft visual identity mobile first`

Archivos del commit:

- `DCFT_VISUAL_IDENTITY_IMPLEMENTATION_REPORT.md`
- `apps/frontend/public/dcft-icon.svg`
- `apps/frontend/src/App.tsx`
- `apps/frontend/src/styles.css`

Cambios backend no relacionados encontrados y no tocados:

- `apps/backend/app/db/bootstrap.py`
- `apps/backend/app/db/models.py`
- `apps/backend/app/db/repositories.py`
- `apps/backend/app/main.py`
- `apps/backend/app/schemas/common.py`
- `apps/backend/app/services/auth_service.py`
- `apps/backend/tests/test_operational_backend.py`
- `apps/backend/alembic/versions/0003_heart_a1_domain_identity.py`
- `apps/backend/alembic/versions/0004_heart_a1_user_plan_assignments.py`
- `apps/backend/alembic/versions/0005_heart_a2_sunat_foundation.py`
- `apps/backend/app/api/identity.py`
- `apps/backend/app/api/sunat.py`
- `apps/backend/app/services/identity_service.py`
- `apps/backend/app/services/sunat_service.py`

## Evidencia de produccion antes de aplicar

URL `https://dcft.vercel.app`:

- Resultado: 404
- Causa probable: dominio/proyecto Vercel no existe, no esta asignado o no tiene deployment activo.

URL `https://dcft-frontend.vercel.app`:

- Resultado: 200
- Bundle JS anterior: `/assets/index-C2M4p6Is.js`
- Bundle CSS anterior: `/assets/index-yCqgIHQK.css`
- `Semaforo Empresarial`: no encontrado
- `Centro Premium de Salud Empresarial`: no encontrado
- Comentario CSS oficial: no encontrado
- Texto `Backend API URL is not configured`: presente en el bundle

Backend esperado:

- `https://dcft-backend.onrender.com/health`: 404
- `https://dcft-backend.onrender.com/runtime/status`: 404

## Evidencia local antes del push

Build local ejecutado:

`npm run build`

Resultado:

- PASS
- JS local generado: `apps/frontend/dist/assets/index-BXNlzv0v.js`
- CSS local generado: `apps/frontend/dist/assets/index-CoE5IPZZ.css`

El bundle local contiene:

- `Semaforo Empresarial`: SI
- `Centro Premium de Salud Empresarial`: SI
- `Medico de Cabecera Empresarial`: SI

## Accion aplicada

Se ejecuto:

`git push origin main`

Resultado:

`aa5fb6d..e8bbc91 main -> main`

## Evidencia de produccion despues del push

URL validada:

`https://dcft-frontend.vercel.app`

Produccion sirve ahora:

- JS: `/assets/index-BXNlzv0v.js`
- CSS: `/assets/index-CoE5IPZZ.css`

El JS productivo contiene:

- `Semaforo Empresarial`: SI
- `Centro Premium de Salud Empresarial`: SI
- `Medico de Cabecera Empresarial`: SI

Validacion visual renderizada en navegador:

- `Semaforo Empresarial`: visible
- `Salud Empresarial`: visible
- `Medico de Cabecera Empresarial`: visible
- Senales de demo anterior: no visibles
- Errores de consola: 0

Texto visible de degradacion:

`Backend API URL is not configured. Runtime degradado.`

## Causa exacta del frontend degradado

Archivo:

`apps/frontend/src/lib/api.ts`

La aplicacion lee:

`import.meta.env.VITE_DCFT_API_URL`

Si no existe en produccion, queda vacia:

`API_URL = ""`

Entonces cualquier llamada API lanza:

`Backend API URL is not configured`

El build productivo actual no contiene `dcft-backend.onrender.com`, por lo que `VITE_DCFT_API_URL` no fue inyectada en Vercel Production.

Ademas, aunque se configurara con `https://dcft-backend.onrender.com`, ese backend actualmente devuelve 404 en `/health` y `/runtime/status`.

## Estado final

Produccion visual oficial:

SI

Source-to-live frontend:

SI, para la visual oficial `e8bbc91`.

Runtime frontend:

DEGRADADO.

Causa:

`VITE_DCFT_API_URL` ausente en Vercel Production y backend live no validado.

URL frontend oficial actual:

`https://dcft-frontend.vercel.app`

URL `https://dcft.vercel.app`:

NO operativa, devuelve 404.

Backend live:

NO validado.

## Pendiente exacto

Para eliminar el runtime degradado falta:

1. Definir la URL backend oficial live.
2. Crear/reparar el backend productivo o staging.
3. Verificar:
   - `/health` 200
   - `/runtime/status` 200
4. Configurar en Vercel Production:
   - `VITE_DCFT_API_URL=<backend-live-url>`
5. Redeploy de Vercel frontend.

Sin esos pasos no es honesto declarar runtime PASS.

