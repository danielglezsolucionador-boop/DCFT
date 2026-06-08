# DCFT Email + Payment Provider Setup Guide

Fecha local: 2026-06-07

## Estado operativo

Bloque email/checkout preparado localmente; pendiente configuracion de proveedores reales.

No hacer push, deploy ni activacion productiva hasta confirmar variables y brechas.

## Regla CEO

- No declarar cierre funcional productivo.
- No elevar estado sin decision CEO.
- No pasar al Doctor estudiante hasta cerrar email verification real o registrar decision explicita del CEO.
- No pedir ni pegar secretos por chat.
- No imprimir secretos en reportes, logs ni screenshots.

## 1. Email provider recomendado por el codigo actual

El backend soporta dos proveedores de correo:

- `smtp`
- `resend`

No hay implementacion actual para:

- SendGrid
- Mailgun
- Amazon SES directo
- Postmark
- otro proveedor API distinto de Resend

Recomendacion operativa para Vercel Production: `resend`, porque el codigo ya llama HTTPS a `https://api.resend.com/emails` y evita configurar SMTP/TLS manual dentro del runtime serverless.

## 2. Variables email exactas para Vercel Production

Variables comunes:

```text
APP_PUBLIC_URL=https://dcft-frontend.vercel.app
EMAIL_PROVIDER=resend
EMAIL_FROM=<verified-sender>
EMAIL_API_KEY=<set-in-vercel-secret>
```

Si el CEO decide usar SMTP en lugar de Resend:

```text
APP_PUBLIC_URL=https://dcft-frontend.vercel.app
EMAIL_PROVIDER=smtp
EMAIL_FROM=<verified-sender>
SMTP_HOST=<smtp-host>
SMTP_PORT=587
SMTP_USER=<set-in-vercel-secret-if-required>
SMTP_PASSWORD=<set-in-vercel-secret-if-required>
```

Notas del codigo:

- Para `resend`, el backend exige `EMAIL_API_KEY` y `EMAIL_FROM`.
- Para `smtp`, el backend exige `SMTP_HOST` y `EMAIL_FROM`.
- `SMTP_USER` y `SMTP_PASSWORD` son opcionales en la condicion del codigo, pero normalmente son necesarios para un proveedor SMTP real.
- `APP_PUBLIC_URL` construye el enlace `/?verify_email_token=...`.

## 3. Endpoints email

Emision inicial:

- `POST /onboarding/tenants`
- Crea cuenta, deja `email_verified=false`, genera token y llama al envio de correo.

Reenvio:

- `POST /auth/resend-verification`
- Body: `{"username":"correo@dominio.com"}`
- Genera nuevo token, consume tokens anteriores no usados y llama al envio de correo.

Verificacion:

- `GET /auth/verify-email?token=<token>`
- Verifica hash del token, expiracion y consumo; marca `users.email_verified=true`.

Flujo frontend:

- El correo apunta a `APP_PUBLIC_URL/?verify_email_token=<token>`.
- El frontend lee `verify_email_token` y llama al backend `GET /auth/verify-email?token=...`.

## 4. Verificacion tecnica email

Existe en codigo:

- Generacion de token con `secrets.token_urlsafe(32)`.
- Hash SHA-256 del token antes de guardar.
- Expiracion de 24 horas.
- Tabla `email_verification_tokens`.
- Campos `users.email_verified` y `users.email_verified_at`.
- Login bloqueado si `email_verified=false`.
- Reenvio de verificacion.
- Mensaje HTML/texto basico.
- Link basado en `APP_PUBLIC_URL`.

Falta o requiere decision:

- Plantilla visual final de marca.
- Politica de dominio remitente y SPF/DKIM/DMARC fuera del codigo.
- Validacion productiva real de entrega/bandeja spam.

## 5. Payment provider soportado por el codigo actual

El backend soporta creacion de checkout con:

- `stripe`

No hay implementacion actual para:

- Mercado Pago
- Culqi
- PayPal
- Niubiz
- Izipay
- otro proveedor de pago

El codigo crea una sesion real en:

```text
https://api.stripe.com/v1/checkout/sessions
```

## 6. Variables payment exactas para Vercel Production

Variables para creacion de checkout Stripe:

```text
APP_PUBLIC_URL=https://dcft-frontend.vercel.app
PAYMENT_PROVIDER=stripe
PAYMENT_SECRET_KEY=<set-in-vercel-secret>
```

Variables ya declaradas pero no usadas para cierre completo del pago:

```text
PAYMENT_PUBLIC_KEY=<set-in-vercel-secret>
PAYMENT_WEBHOOK_SECRET=<set-in-vercel-secret>
```

Notas del codigo:

- `PAYMENT_SECRET_KEY` se usa para llamar Stripe Checkout.
- `PAYMENT_PUBLIC_KEY` esta en configuracion, pero el backend actual no la usa.
- `PAYMENT_WEBHOOK_SECRET` esta en configuracion, pero no existe endpoint webhook que lo valide.
- `APP_PUBLIC_URL` se usa para `success_url` y `cancel_url`.

## 7. Endpoints payment

Estado del proveedor:

- `GET /subscriptions/checkout/status`

Crear checkout:

- `POST /subscriptions/checkout`
- Body: `{"plan":"mype","billing_cycle":"monthly"}`
- Body: `{"plan":"mype","billing_cycle":"annual"}`
- Body: `{"plan":"premium","billing_cycle":"monthly"}`
- Body: `{"plan":"premium","billing_cycle":"annual"}`

Webhook:

- No existe endpoint webhook implementado.
- No existe validacion de firma Stripe.
- No existe procesamiento de `checkout.session.completed`.
- No existe activacion automatica de MYPE/Premium por pago confirmado.

## 8. Precios implementados

```text
student: S/ 0
mype monthly: S/ 89 / mes -> 8900 centimos PEN
mype annual: S/ 890 / anio -> 89000 centimos PEN
premium monthly: S/ 199 / mes -> 19900 centimos PEN
premium annual: S/ 1,990 / anio -> 199000 centimos PEN
```

## 9. Persistencia payment/subscription

Existe:

- Tabla `checkout_sessions`.
- Tabla `subscriptions`.
- Campos de sesion: tenant, user, plan, billing cycle, provider, provider session id, checkout URL, amount, currency, status.

No existe:

- Tabla `payments`.
- Tabla `payment_events`.
- Tabla `stripe_webhook_events`.
- Funcion que marque checkout como paid.
- Funcion que valide firma webhook.
- Funcion que active plan desde evento de pago.

Activacion actual de plan:

- Existe `subscription_service.change_plan(...)`.
- Puede cambiar plan via endpoints internos/autorizados.
- No esta conectado a Stripe ni a confirmacion de pago.
- Por lo tanto, no debe tratarse como activacion comercial automatica.

## 10. Como configurar sin pegar secretos en chat

1. Abrir Vercel Project Settings.
2. Entrar a Environment Variables.
3. Seleccionar Production.
4. Crear o actualizar variables por nombre exacto.
5. Pegar cada secreto solo en Vercel, no en chat.
6. No registrar capturas que muestren valores.
7. No ejecutar comandos que impriman variables completas.

## 11. Como validar sin imprimir secretos

Email:

1. Confirmar que `EMAIL_PROVIDER` y `EMAIL_FROM` existen por nombre en Vercel.
2. Crear una cuenta de prueba con correo controlado.
3. Verificar que la respuesta de onboarding diga `email_verification.required=true`.
4. Confirmar recepcion del correo en bandeja real.
5. Abrir el link recibido.
6. Confirmar que `GET /auth/verify-email?token=...` responde con correo confirmado.
7. Intentar login despues de confirmar.

Payment:

1. Confirmar que `PAYMENT_PROVIDER=stripe` y `PAYMENT_SECRET_KEY` existen por nombre en Vercel.
2. Usar cuenta de prueba, no cliente real.
3. Solicitar checkout MYPE mensual y verificar que retorna `checkout_url`.
4. No considerar el plan activado despues de pagar porque falta webhook.
5. No vender activacion automatica hasta implementar webhook y firma.

## 12. URLs a probar

Frontend:

```text
https://dcft-frontend.vercel.app
https://dcft-frontend.vercel.app/?access=business
```

Backend:

```text
https://dcft.vercel.app/health
https://dcft.vercel.app/runtime/status
https://dcft.vercel.app/auth/resend-verification
https://dcft.vercel.app/auth/verify-email?token=<token-from-email>
https://dcft.vercel.app/subscriptions/checkout/status
https://dcft.vercel.app/subscriptions/checkout
```

## 13. Que NO hacer

- No pegar claves reales en chat.
- No guardar secretos en Markdown.
- No hacer deploy hasta decidir si basta con email real o si tambien se exige webhook payment.
- No declarar pago completo con solo crear Stripe Checkout.
- No activar MYPE/Premium manualmente como si fuera pago confirmado.
- No habilitar SUNAT real dentro de este bloque.
- No pasar a empresa desde estudiante por este bloque.
- No continuar Doctor estudiante si el CEO exige cerrar antes email verification real.

## 14. Brecha critica antes de produccion comercial

Email puede cerrarse con variables reales de Resend o SMTP.

Checkout Stripe puede abrir sesion real, pero el ciclo comercial esta incompleto porque falta:

- endpoint webhook,
- validacion de firma,
- persistencia de evento de pago,
- actualizacion de `checkout_sessions.status`,
- activacion de plan via pago confirmado,
- pruebas de ciclo mensual/anual.
