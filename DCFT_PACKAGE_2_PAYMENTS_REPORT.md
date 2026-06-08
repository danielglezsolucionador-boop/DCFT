# DCFT Package 2 Payments Report

Fecha/hora: 2026-06-08 00:48:13 -05:00

Estado: paquete de pagos cerrado localmente; pendiente configuracion real Stripe y autorizacion CEO/CTO para produccion.

## Fuente maestra

- Comercial primaria: `C:\Users\admin\Desktop\entregar a codex la app doctor cft\DCFT.docx`.
- Espejo: `C:\Users\admin\Desktop\dcft.txt`.
- Soporte planes: fases `1.2`, `1.7`, `10.2`, `10.3` en `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613`.

## Backup

- Backup pre-cambio: `D:\ECOSYSTEM\BACKUPS\dcft-package-2-payments-prechange-20260608-004240.zip`.
- Excluido: `.env`, `.vercel`, `node_modules`, `.venv`, `dist/build`, logs, caches y bytecode.

## Git

- HEAD base: `e5e00f4`.
- No se hizo commit.
- No se hizo push.
- No se hizo deploy.
- El arbol ya tenia cambios locales previos; se mantuvieron sin revertir.

## Proveedor oficial

- Pago oficial: Stripe.
- Variables: `PAYMENT_PROVIDER=stripe`, `PAYMENT_SECRET_KEY`, `PAYMENT_PUBLIC_KEY`, `PAYMENT_WEBHOOK_SECRET`, `APP_PUBLIC_URL`.
- No se imprimieron secretos.
- No se pidieron claves por chat.
- No se modifico ni se commiteo `.env`.

## Planes

- Estudiante: S/ 0.
- MYPE mensual: S/ 89.
- MYPE anual: S/ 890.
- Premium mensual: S/ 199.
- Premium anual: S/ 1,990.

Cada plan conserva nombre, precio, intervalo, estado, beneficios visibles y CTA segun configuracion del proveedor.

## Checkout

- Endpoint: `POST /subscriptions/checkout`.
- Crea Stripe Checkout Session real cuando Stripe esta completo.
- Guarda `checkout_sessions` con plan, intervalo, monto, moneda, proveedor, `provider_session_id`, URL y estado `pending`.
- Crear checkout no activa plan.
- Si falta provider, devuelve bloqueo honesto y no muestra pago real.

## Webhook

- Endpoint: `POST /subscriptions/stripe/webhook`.
- Valida firma con `PAYMENT_WEBHOOK_SECRET`.
- Procesa `checkout.session.completed`.
- Registra evento en `stripe_webhook_events`.
- Evita doble activacion con idempotencia.
- Valida metadata contra tenant/user/plan/billing cycle.
- Valida amount/currency contra la sesion interna.
- Guarda `paid_at`, `provider_customer_id`, `provider_subscription_id`, monto, moneda y estado.

## Activacion

- La activacion ocurre solo con webhook firmado.
- MYPE/Premium se sincronizan en `subscriptions`, `users` y `user_business_plans`.
- Mensual/anual se guarda en `billing_cycle`; intervalo visible `monthly` o `yearly`.
- No hay pago falso ni activacion por boton local.

## Suscripcion

- Endpoint nuevo: `GET /subscriptions/status`.
- Devuelve `plan`, `status`, `trial`, `started_at`, `ends_at`, `billing_cycle`, `interval`, `provider`, `payment_status`, `checkout` y `subscription`.
- `GET /subscriptions/current` se mantiene para compatibilidad.
- `GET /subscriptions/checkout/status` se mantiene para provider/plans/checkout readiness.

## UI planes

- Si Stripe falta: no muestra `Pagar ahora`; muestra `Pago pendiente de configuracion` y `Solicitar activacion`.
- Si Stripe esta completo: muestra `Pagar MYPE mensual`, `Pagar MYPE anual`, `Pagar Premium mensual`, `Pagar Premium anual`.
- MYPE/Premium permanecen como camino comercial visible.

## Tests

- Crear checkout no activa plan.
- Webhook firmado activa plan.
- Webhook invalido rechaza.
- Webhook duplicado no duplica.
- MYPE mensual activa correctamente.
- MYPE anual activa correctamente.
- Premium mensual activa correctamente.
- Premium anual activa correctamente.
- Frontend no muestra pagar si provider falta.
- Status devuelve plan correcto.

Resultado: 48 tests PASS.

## Build y validaciones

- `npm run build`: PASS.
- `python -m compileall apps\backend api -q`: PASS.
- `$env:PYTHONPATH='apps/backend'; python -m pytest -q`: PASS, 48 tests.
- `git diff --check`: PASS, warnings CRLF solamente.
- Secret scan: REVIEW_FILES_ONLY por placeholders de test; no se imprimieron valores.

## Produccion

- No push.
- No deploy.
- Produccion no refleja este paquete.
- Para producir, CEO/CTO debe configurar variables reales y autorizar despliegue controlado.

## No tocado

- SUNAT real.
- FORJA.
- CEREBRO.
- SENTINELA.
- Ecosistema.
- Local Agent.
- Runtimes externos.

## Riesgos

- Falta configurar Stripe real en Vercel Production.
- Falta crear webhook en Stripe Dashboard apuntando al backend productivo.
- Falta validar evento real controlado antes de exposicion comercial.
- Secret scan marca placeholders de test, no secretos reales.

## Recomendacion

Configurar variables Stripe en Vercel/secret manager sin pegarlas en chat, crear el webhook productivo en Stripe Dashboard y autorizar deploy controlado con prueba real de bajo riesgo.
