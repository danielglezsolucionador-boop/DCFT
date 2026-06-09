# DCFT Email, Payment and AI Provider Setup Guide

Fecha local: 2026-06-07

## Estado permitido

Bloque email/checkout/Doctor preparado localmente; pendiente configuracion de proveedores reales y autorizacion CEO/CTO para deploy controlado.

No push. No deploy. No produccion.

## Proveedores oficiales CEO/CTO

Desde 2026-06-08, los proveedores objetivo para DCFT son:

- Email: Resend.
- Email fallback: SMTP.
- Payment: Mercado Pago.
- AI Doctor estudiante: OpenRouter.

No proponer otro proveedor como principal. Cualquier otro soporte existente en codigo queda como compatibilidad secundaria/no objetivo hasta decision explicita CEO/CTO.

## 1. Email

Proveedor objetivo oficial: Resend.

Fallback oficial soportado: SMTP.

Endpoints:

- `POST /auth/resend-verification`
- `GET /auth/verify-email?token=...`
- El correo se emite desde onboarding y reenvio de verificacion.

Variables para Vercel Production:

- `APP_PUBLIC_URL`
- `EMAIL_PROVIDER`
- `EMAIL_FROM`
- `EMAIL_API_KEY`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`

Configuracion Resend:

- `EMAIL_PROVIDER=resend`
- `EMAIL_FROM` debe ser un remitente validado en Resend.
- `EMAIL_API_KEY` debe cargarse solo como Environment Variable secreta en Vercel.
- `APP_PUBLIC_URL` debe apuntar al frontend publico real.

Configuracion SMTP:

- `EMAIL_PROVIDER=smtp`
- `EMAIL_FROM`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`

Comportamiento si falta proveedor:

- No simula envio.
- Devuelve `email_provider_missing=true`.
- Login sigue bloqueando cuenta no verificada.

## 2. Payment

Proveedor objetivo oficial soportado por el codigo actual: Mercado Pago.

Stripe queda como proveedor secundario legado solo si CEO/CTO lo reactivan expresamente.

Endpoint de checkout:

- `POST /subscriptions/checkout`

Endpoint de webhook:

- `POST /subscriptions/mercadopago/webhook`
- `POST /subscriptions/stripe/webhook`

Eventos procesados:

- Mercado Pago: `subscription_authorized_payment` y `payment` con estado aprobado consultado al proveedor.
- `checkout.session.completed`

Variables para Vercel Production:

- `PAYMENT_PROVIDER=mercadopago`
- `MERCADOPAGO_ACCESS_TOKEN`
- `MERCADOPAGO_PUBLIC_KEY`
- `MERCADOPAGO_WEBHOOK_SECRET`
- `APP_PUBLIC_URL`

Variables secundarias Stripe solo si CEO/CTO reactivan Stripe:

- `PAYMENT_PROVIDER=stripe`
- `PAYMENT_SECRET_KEY`
- `PAYMENT_PUBLIC_KEY`
- `PAYMENT_WEBHOOK_SECRET`

Regla de seguridad:

- Mercado Pago se considera operativo solo si existen `PAYMENT_PROVIDER=mercadopago`, `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_PUBLIC_KEY`, `MERCADOPAGO_WEBHOOK_SECRET` y `APP_PUBLIC_URL`.
- Crear checkout no activa plan.
- Solo webhook firmado activa plan.
- Webhook duplicado no duplica activacion.

Planes:

- Estudiante: `S/ 0`
- MYPE mensual: `S/ 89 / mes`
- MYPE anual: `S/ 890 / año`
- Premium mensual: `S/ 199 / mes`
- Premium anual: `S/ 1,990 / año`

## 3. AI

Proveedor objetivo oficial para Doctor estudiante: OpenRouter.

Variables oficiales para Vercel Production:

- `AI_PROVIDER=openrouter`
- `OPENROUTER_API_KEY`
- `AI_MODEL` o `AI_DEFAULT_MODEL`

Variables DCFT equivalentes soportadas por el backend:

- `DCFT_AI_PROVIDER_ENABLED`
- `DCFT_AI_PROVIDER=openrouter`
- `DCFT_AI_MODEL`
- `DCFT_OPENROUTER_API_KEY`
- `DCFT_OPENROUTER_MODEL`
- `DCFT_OPENROUTER_BASE_URL`
- `DCFT_OPENROUTER_REFERER`
- `DCFT_OPENROUTER_TITLE`

Soporte secundario/no objetivo detectado en codigo:

- `DCFT_OPENAI_API_KEY`
- `DCFT_ANTHROPIC_API_KEY`
- `DCFT_GEMINI_API_KEY`

Estas rutas secundarias no cambian la decision oficial: OpenRouter es el proveedor objetivo para el Doctor estudiante.

Comportamiento si falta proveedor IA:

- Doctor estudiante no descuenta cuota.
- Devuelve `ai_provider_missing=true`.
- UI debe mostrar: `Disponible cuando se configure proveedor IA.`

## 4. Pasos Vercel Production

1. Entrar a Vercel Project Settings.
2. Abrir Environment Variables.
3. Seleccionar Production.
4. Crear cada variable por nombre exacto.
5. Pegar cada secreto directamente en Vercel, nunca en chat ni documentos.
6. Guardar variables.
7. No redeployar hasta autorizacion CEO/CTO.

## 5. Validacion sin imprimir secretos

No usar `echo` sobre variables secretas.

Validaciones permitidas:

- Verificar presencia por nombre desde panel Vercel.
- Ejecutar health/status sin imprimir valores.
- Probar login no verificado y confirmar bloqueo.
- Probar reenvio de correo y confirmar que no devuelve `email_provider_missing=true`.
- Crear checkout solo con Mercado Pago completo y confirmar status `pending`.
- Enviar webhook firmado desde Mercado Pago Developers y confirmar plan activo.
- Probar Doctor con proveedor IA y confirmar que una respuesta exitosa descuenta 1 de 5.
- Probar Doctor sin proveedor IA y confirmar que no descuenta.

## 6. URLs a probar

- Frontend: `APP_PUBLIC_URL`
- Backend health: `/health`
- Estado runtime: `/runtime/status`
- Reenvio email: `POST /auth/resend-verification`
- Verificacion email: `GET /auth/verify-email?token=...`
- Planes: `GET /subscriptions/plans`
- Estado suscripcion: `GET /subscriptions/status`
- Estado checkout: `GET /subscriptions/checkout/status`
- Checkout: `POST /subscriptions/checkout`
- Webhook Mercado Pago: `POST /subscriptions/mercadopago/webhook`
- Webhook Stripe secundario: `POST /subscriptions/stripe/webhook`
- Doctor status: `GET /student/doctor/status`
- Doctor ask: `POST /student/doctor/ask`

## 7. Que NO hacer

- No pegar secretos en chat.
- No subir `.env`.
- No imprimir claves en logs.
- No activar plan por crear checkout.
- No aceptar webhook sin firma.
- No descontar cuota Doctor si falta proveedor IA.
- No simular correo enviado.
- No tocar SUNAT real.
- No hacer deploy sin variables reales y autorizacion CEO/CTO.

## 8. Actualizacion Paquete 2 Pagos Mercado Pago - 2026-06-08

### Mercado Pago Production requerido

Variables exactas:

- `PAYMENT_PROVIDER=mercadopago`
- `MERCADOPAGO_ACCESS_TOKEN`
- `MERCADOPAGO_PUBLIC_KEY`
- `MERCADOPAGO_WEBHOOK_SECRET`
- `APP_PUBLIC_URL`

### Flujo de activacion

1. Usuario elige MYPE o Premium.
2. Usuario elige mensual o anual.
3. `POST /subscriptions/checkout` crea preapproval Mercado Pago.
4. La sesion interna queda `pending`.
5. Mercado Pago envia `subscription_authorized_payment` o `payment`.
6. `POST /subscriptions/mercadopago/webhook` valida firma `x-signature`.
7. Backend consulta Mercado Pago y exige pago aprobado.
8. Backend valida monto y moneda contra checkout interno.
9. Backend activa plan y guarda periodo.
10. `GET /subscriptions/status` refleja plan activo y pago `paid`.

### Planes oficiales

- Estudiante: S/ 0.
- MYPE mensual: S/ 89.
- MYPE anual: S/ 890.
- Premium mensual: S/ 199.
- Premium anual: S/ 1,990.

### No hacer

- No activar MYPE/Premium por crear checkout.
- No aceptar webhook sin firma.
- No registrar pago sin confirmacion Mercado Pago verificada.
- No imprimir secretos.
- No hacer deploy hasta autorizacion CEO/CTO.

## 9. Cierre V1 para revision CEO en produccion - 2026-06-08

### Proveedores oficiales

Email:

- Proveedor objetivo: Resend.
- Fallback: SMTP.
- Si no hay proveedor configurado, el backend debe bloquear el envio con mensaje claro y no simular correo enviado.

Pagos:

- Proveedor objetivo: Mercado Pago.
- Si falta `PAYMENT_PROVIDER=mercadopago`, `MERCADOPAGO_ACCESS_TOKEN`, `MERCADOPAGO_PUBLIC_KEY` o `MERCADOPAGO_WEBHOOK_SECRET`, el checkout real debe quedar bloqueado.
- Crear checkout no activa MYPE/Premium.
- Solo `POST /subscriptions/mercadopago/webhook` con firma valida y pago aprobado activa plan.

IA:

- Proveedor objetivo: OpenRouter.
- Si falta proveedor o API key, el Doctor estudiante queda bloqueado con mensaje claro y no descuenta cuota.

### Variables a revisar en Vercel Production sin imprimir valores

- `APP_PUBLIC_URL`
- `EMAIL_PROVIDER`
- `EMAIL_FROM`
- `EMAIL_API_KEY`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `PAYMENT_PROVIDER`
- `MERCADOPAGO_ACCESS_TOKEN`
- `MERCADOPAGO_PUBLIC_KEY`
- `MERCADOPAGO_WEBHOOK_SECRET`
- `AI_PROVIDER`
- `OPENROUTER_API_KEY`
- `AI_MODEL`
- `AI_DEFAULT_MODEL`
- `DCFT_AI_PROVIDER`
- `DCFT_OPENROUTER_API_KEY`
- `DCFT_AI_MODEL`
- `DCFT_OPENROUTER_MODEL`

### URLs de validacion posterior al deploy

- Frontend: `https://dcft-frontend.vercel.app`
- Backend health: `https://dcft.vercel.app/health`
- Backend runtime: `https://dcft.vercel.app/runtime/status`
- Planes: `GET /subscriptions/plans`
- Estado checkout: `GET /subscriptions/checkout/status`
- Estado Doctor: `GET /student/doctor/status`

### No hacer en revision CEO

- No pegar secretos en chat.
- No ejecutar `echo` de variables secretas.
- No subir `.env`.
- No activar SUNAT real.
- No presentar bloqueos de proveedor como funciones ya configuradas.
