# DCFT Final V1 Pre CEO Review Report

Fecha local: 2026-06-08
Repositorio oficial: `C:\Users\admin\dcft-knowledge-core`

## Estado

DCFT V1 se consolida localmente para commit, push y deploy de revision CEO.
No se declara aprobacion final.

Estado maximo permitido despues de produccion validada:

`DCFT V1 listo para revision CEO en produccion.`

## Backup final usado

- Ruta: `D:\ECOSYSTEM\BACKUPS\dcft-final-v1-pre-ceo-review-20260608-010945.zip`
- Tamano verificado: 45,523,169 bytes.
- Equivalente reportado: 43.41 MB.
- Entradas reportadas: 4000.
- Exclusiones reportadas: `.env`, `.vercel`, `node_modules`, `.venv`, `dist`, logs, `*.pyc`.

## Commit base antes de consolidar

- HEAD inicial: `e5e00f4 fix: refine dcft student review flow`.
- Rama: `main`.
- Destino autorizado: `origin/main`.

## Paquete 1 - Estudiante

Incluye:

- Selector estudiante/empresa intacto.
- Seccion estudiante operativa.
- Registro estudiante con verificacion de email.
- Login bloqueado si email no esta verificado.
- Reenvio de verificacion.
- Doctor estudiante con proveedor IA objetivo OpenRouter.
- Cuota estudiante: 5 preguntas mensuales.
- Proveedor IA faltante bloquea sin descontar cuota.
- 30 ejercicios visibles.
- Plan Contable visible.
- Beneficios sin duplicados.
- Beneficios activos separados de proximamente.
- Modulos empresariales tenues.
- PDF propio y Doctor estudiante tratados como funciones dependientes de proveedor/configuracion.

Archivos principales:

- `apps/backend/app/api/auth.py`
- `apps/backend/app/api/student.py`
- `apps/backend/app/services/auth_service.py`
- `apps/backend/app/services/email_service.py`
- `apps/backend/app/services/student_doctor_service.py`
- `apps/backend/app/db/models.py`
- `apps/backend/app/db/repositories.py`
- `apps/frontend/src/App.tsx`
- `apps/frontend/src/lib/api.ts`
- `apps/frontend/src/styles.css`
- `apps/backend/alembic/versions/0009_email_verification_checkout.py`
- `apps/backend/alembic/versions/0010_student_doctor_usage.py`

## Paquete 2 - Pagos

Incluye:

- Plan Estudiante S/ 0.
- MYPE S/ 89 mensual y S/ 890 anual.
- Premium S/ 199 mensual y S/ 1,990 anual.
- `GET /subscriptions/plans`.
- `GET /subscriptions/status`.
- `GET /subscriptions/checkout/status`.
- `POST /subscriptions/checkout`.
- `POST /subscriptions/stripe/webhook`.
- Checkout Stripe real cuando `PAYMENT_PROVIDER=stripe` y variables estan presentes.
- Checkout no activa plan por si solo.
- Webhook firmado activa MYPE/Premium.
- Firma invalida rechaza.
- Evento duplicado no duplica activacion.
- Estado de suscripcion devuelve plan/status/ciclo/proveedor.
- Stripe faltante bloquea con mensaje claro, sin pago falso.

Archivos principales:

- `apps/backend/app/api/subscriptions.py`
- `apps/backend/app/services/payment_service.py`
- `apps/backend/app/services/subscription_service.py`
- `apps/backend/app/db/models.py`
- `apps/backend/app/db/repositories.py`
- `apps/backend/alembic/versions/0009_email_verification_checkout.py`
- `apps/backend/alembic/versions/0011_stripe_webhook_activation.py`
- `apps/frontend/src/App.tsx`
- `apps/frontend/src/lib/api.ts`
- `apps/frontend/src/styles.css`

## Paquete 3 - Empresa y SUNAT auxiliar

Incluye:

- Entrada empresa MYPE/Premium.
- RUC.
- Razon social.
- Correo.
- Contrasena.
- Usuario secundario SUNAT.
- Clave secundaria SUNAT.
- Consentimiento obligatorio.
- `Ver seguridad`.
- Vault local/seguro para credencial auxiliar.
- Status y desconexion.
- Usuario enmascarado.
- Password no retorna al frontend.
- SUNAT real automatico apagado.
- Piloto asistido documentado.

Archivos principales:

- `apps/backend/app/services/onboarding_service.py`
- `apps/backend/app/db/models.py`
- `apps/backend/app/db/repositories.py`
- `apps/backend/app/schemas/common.py`
- `apps/frontend/src/App.tsx`
- `apps/frontend/src/styles.css`

## Proveedores objetivo

Email:

- Objetivo: Resend.
- Fallback: SMTP.
- Variables: `APP_PUBLIC_URL`, `EMAIL_PROVIDER`, `EMAIL_FROM`, `EMAIL_API_KEY`, `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`.

Pagos:

- Objetivo: Stripe.
- Variables: `PAYMENT_PROVIDER=stripe`, `PAYMENT_SECRET_KEY`, `PAYMENT_PUBLIC_KEY`, `PAYMENT_WEBHOOK_SECRET`, `APP_PUBLIC_URL`.

IA:

- Objetivo: OpenRouter.
- Variables: `AI_PROVIDER=openrouter`, `OPENROUTER_API_KEY`, `AI_MODEL` o `AI_DEFAULT_MODEL`.
- Compatibilidad backend DCFT: `DCFT_AI_PROVIDER`, `DCFT_OPENROUTER_API_KEY`, `DCFT_AI_MODEL`, `DCFT_OPENROUTER_MODEL`.

No se incluyen valores reales.

## Produccion esperada

Frontend:

- `https://dcft-frontend.vercel.app`

Backend:

- `https://dcft.vercel.app/health`
- `https://dcft.vercel.app/runtime/status`

Runtime esperado:

- `postgres=true`
- `sqlite=false`
- `persistent=true`
- `temporal=false`
- `real_connector_enabled=false`
- `real_sunat_session=false`
- `remote_actions_enabled=false`

SUNAT real debe permanecer apagado.

## Validaciones locales requeridas antes de commit

- `npm run build` en `apps/frontend`.
- `python -m compileall apps\backend api -q`.
- `python -m pytest -q`.
- `git diff --check`.
- Secret scan sin secretos reales.

## Reportes incluidos en consolidacion

- `DCFT_OPERATIONAL_V1_CEO_REPORT.md`
- `DCFT_EMAIL_PAYMENT_AI_PROVIDER_SETUP_GUIDE.md`
- `DCFT_PACKAGE_1_STUDENT_COMPLETE_REPORT.md`
- `DCFT_PACKAGE_2_PAYMENTS_REPORT.md`
- `DCFT_PACKAGE_3_COMPANY_SUNAT_REPORT.md`
- `DCFT_CHECKOUT_STRIPE_WEBHOOK_IMPLEMENTATION_REPORT.md`
- `DCFT_EMAIL_VERIFICATION_IMPLEMENTATION_REPORT.md`
- `DCFT_STUDENT_DOCTOR_REAL_IMPLEMENTATION_REPORT.md`
- `DCFT_PILOTO_ASISTIDO_EMPRESA_AUTORIZADA_REPORT.md`
- `DCFT_GUIA_EMPRESA_PILOTO_SUNAT_AUXILIAR.md`

## Riesgos pendientes

- Produccion puede quedar bloqueada si Vercel no tiene variables reales de Resend/SMTP, Stripe u OpenRouter.
- Si faltan variables, el comportamiento correcto es bloqueo claro, no simulacion.
- SUNAT real no debe activarse sin autorizacion explicita.
- El deploy necesita espera hasta estado Ready y validacion posterior.

## Incidente de deploy y reparacion

- Primer deploy del commit `bc044f6` dejo frontend HTTP 200 y runtime HTTP 200, pero `/health` empezo a devolver HTTP 500.
- Log Vercel: columna faltante `subscriptions.billing_cycle` en Postgres persistente.
- Causa: bootstrap consultaba `Subscription` antes de preparar columnas nuevas de checkout/suscripcion cuando `DCFT_DB_AUTO_MIGRATE=false`.
- Reparacion quirurgica: `bootstrap_local_identity()` ahora ejecuta `ensure_checkout_storage()`, `ensure_stripe_webhook_storage()` y `ensure_student_doctor_storage()` antes de leer `subscriptions`.
- No toca SUNAT real.
- No imprime secretos.
- No activa pagos ni proveedores por si solo.

## Recomendacion

Si las validaciones locales pasan, hacer commit selectivo, push a `origin/main`, esperar Vercel Ready y validar produccion movil 390x844 antes de entregar el estado de revision CEO.
