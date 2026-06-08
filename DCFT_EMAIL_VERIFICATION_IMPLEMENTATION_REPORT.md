# DCFT Email Verification Implementation Report

Fecha local: 2026-06-07

## Estado

Listo para revisión CEO.

## Implementado

- Nuevos usuarios de onboarding se crean con `email_verified=false` y `active=false`.
- Login con contraseña correcta queda bloqueado si falta confirmación.
- Mensaje de login: `Confirma tu correo para activar tu cuenta.`
- Token seguro generado con `secrets.token_urlsafe`.
- Solo se persiste `sha256(token)`.
- Expiración: 24 horas.
- Endpoint de confirmación: `GET /auth/verify-email?token=...`.
- Endpoint de reenvío: `POST /auth/resend-verification`.
- Si falta proveedor: `email_provider_missing=true`.
- Mensaje provider missing: `Falta configurar proveedor de correo para activar cuentas.`
- Soporte real inicial para SMTP y Resend.

## Archivos

- `apps/backend/app/services/email_service.py`
- `apps/backend/app/api/auth.py`
- `apps/backend/app/services/auth_service.py`
- `apps/backend/app/services/onboarding_service.py`
- `apps/backend/app/db/models.py`
- `apps/backend/app/db/repositories.py`
- `apps/backend/alembic/versions/0009_email_verification_checkout.py`
- `.env.example`
- `.env.production.example`
- `.env.staging.example`
- `apps/frontend/src/App.tsx`
- `apps/frontend/src/lib/api.ts`

## Validación

- `python -m compileall apps\backend api -q`: PASS.
- `python -m pytest -q`: PASS, 36 tests.
- `npm run build`: PASS.

## Riesgo

Sin `EMAIL_PROVIDER` y credenciales reales, las cuentas quedan creadas pero no activables por usuario final. Esto es intencional: no se simula correo.
