# DCFT Mercado Pago Payment Provider Report

Fecha local: 2026-06-08 19:08:37 -05:00

## Estado

Mercado Pago queda implementado localmente como proveedor principal de pagos DCFT.

Estado maximo permitido en este bloque: codigo preparado y validado localmente; cobro real pendiente de credenciales reales Mercado Pago y validacion productiva controlada.

## Decision CEO/CTO

- Stripe queda descartado como proveedor principal por bloqueo real de onboarding Peru.
- Proveedor oficial nuevo: Mercado Pago.
- Prioridad posterior: SUNAT auxiliar/piloto y OpenRouter al final.
- No se toco SUNAT real automatico.
- No se toco OpenRouter.
- No se toco correo/dominio.

## Referencias oficiales Mercado Pago

- Crear preferencia Checkout Pro: https://www.mercadopago.com.pe/developers/es/reference/online-payments/checkout-pro/preferences/create-preference/post
- Crear suscripcion/preapproval: https://www.mercadopago.com.pe/developers/es/reference/online-payments/subscriptions/create-preapproval/post
- Crear plan de suscripcion: https://www.mercadopago.com.pe/developers/es/reference/online-payments/subscriptions/create-preapproval-plan/post
- Webhooks Checkout Pro y firma `x-signature`: https://www.mercadopago.com.pe/developers/en/docs/checkout-pro/payment-notifications
- Gestion de suscripciones: https://www.mercadopago.com.pe/developers/en/docs/subscriptions/subscription-management

## Implementacion

### Provider principal

- `PAYMENT_PROVIDER=mercadopago`
- Variables requeridas:
  - `MERCADOPAGO_ACCESS_TOKEN`
  - `MERCADOPAGO_PUBLIC_KEY`
  - `MERCADOPAGO_WEBHOOK_SECRET`
  - `APP_PUBLIC_URL`

### Provider secundario legado

Stripe queda soportado como provider secundario si CEO/CTO lo reactivan expresamente:

- `PAYMENT_PROVIDER=stripe`
- `PAYMENT_SECRET_KEY`
- `PAYMENT_PUBLIC_KEY`
- `PAYMENT_WEBHOOK_SECRET`

## Checkout Mercado Pago

Endpoint DCFT:

- `POST /subscriptions/checkout`

Cuando el provider es Mercado Pago y todas las variables existen:

1. Valida plan y ciclo.
2. Crea sesion interna `checkout_sessions` en estado `creating`.
3. Crea preapproval Mercado Pago en `POST https://api.mercadopago.com/preapproval`.
4. Guarda `provider_session_id`, `checkout_url`, monto, moneda, plan, ciclo y estado `pending`.
5. Devuelve URL de checkout.

No activa MYPE/Premium al crear checkout.

## Recurrencia

Opcion implementada: `preapproval` de Mercado Pago sin plan precreado.

Razon:

- DCFT tiene planes mensuales y anuales.
- `preapproval` permite flujo recurrente con `auto_recurring`.
- Evita tener que crear y sincronizar cuatro planes externos por ahora.

Ciclos:

- Mensual: `frequency=1`, `frequency_type=months`.
- Anual: `frequency=12`, `frequency_type=months`.

Fallback documentado:

- Si la cuenta Mercado Pago no permite recurrente, CEO/CTO debe decidir si se baja a Checkout Pro/preferencia controlada antes de vender anual/mensual como recurrencia real.

## Webhook Mercado Pago

Endpoint DCFT:

- `POST /subscriptions/mercadopago/webhook`

Valida:

- Header `x-signature`.
- Header `x-request-id`.
- Template HMAC SHA256: `id:{data.id};request-id:{x-request-id};ts:{ts};`.
- Tolerancia temporal de 300 segundos.
- Secret: `MERCADOPAGO_WEBHOOK_SECRET`.

Procesa:

- `subscription_authorized_payment`
- `payment`

Para activar plan:

1. Recibe notificacion firmada.
2. Consulta Mercado Pago:
   - `/authorized_payments/{id}` para pagos autorizados de suscripcion.
   - `/v1/payments/{id}` para pagos.
3. Exige estado aprobado.
4. Busca checkout interno pendiente por `external_reference` o `preapproval_id`.
5. Valida monto y moneda.
6. Marca checkout `paid`.
7. Activa suscripcion, plan, ciclo, provider y periodo.
8. Mantiene idempotencia para duplicados.

## Planes

- Estudiante: S/ 0.
- MYPE mensual: S/ 89.
- MYPE anual: S/ 890.
- Premium mensual: S/ 199.
- Premium anual: S/ 1,990.

## UI

- Si Mercado Pago esta configurado, la UI muestra:
  - `Pagar MYPE mensual`
  - `Pagar MYPE anual`
  - `Pagar Premium mensual`
  - `Pagar Premium anual`
- Si Mercado Pago falta, la UI no muestra pago inmediato:
  - `Pago pendiente de configuracion`
  - `Solicitar activacion`

## Tests

Pruebas focalizadas ejecutadas:

- Checkout Mercado Pago no activa plan al crear preapproval.
- Webhook aprobado activa MYPE mensual.
- Webhook aprobado activa MYPE anual.
- Webhook aprobado activa Premium mensual.
- Webhook aprobado activa Premium anual.
- Webhook duplicado no duplica activacion.
- Webhook con firma invalida rechaza.
- Webhook no aprobado no activa plan.
- Stripe no rompe como provider secundario.
- Estado de suscripcion devuelve plan activo.
- UI no muestra pagar cuando provider falta.

Resultado focalizado: PASS, 16 tests.

## Tablas / modelos

- `checkout_sessions`: guarda checkout/preapproval interno, proveedor, plan, ciclo, monto, moneda, URL, estado y pago.
- `subscriptions`: guarda plan activo, provider, ciclo y periodo.
- `stripe_webhook_events`: se reutiliza como ledger de eventos de pago provider-discriminado mediante columna `provider`.

Nota: el nombre fisico de la tabla de eventos conserva legado Stripe para evitar migracion destructiva. La logica nueva guarda `provider=mercadopago`.

## Variables faltantes para cobro real

No se cargaron ni se imprimieron secretos.

Para produccion se deben cargar en Vercel/secret manager:

- `PAYMENT_PROVIDER=mercadopago`
- `MERCADOPAGO_ACCESS_TOKEN`
- `MERCADOPAGO_PUBLIC_KEY`
- `MERCADOPAGO_WEBHOOK_SECRET`
- `APP_PUBLIC_URL=https://dcft-frontend.vercel.app`

Webhook Dashboard Mercado Pago:

- URL: `https://dcft.vercel.app/subscriptions/mercadopago/webhook`
- Eventos minimos:
  - `subscription_authorized_payment`
  - `payment`

## No tocado

- SUNAT real automatico.
- OpenRouter.
- Correo/dominio.
- FORJA.
- CEREBRO.
- SENTINELA.
- Ecosistema.
- `.env` real.

## Riesgos

- Falta validar con credenciales reales de Mercado Pago Peru.
- La cuenta Mercado Pago puede exigir habilitacion especifica para recurrencia/preapproval.
- Si recurrencia no esta disponible, CEO/CTO debe aprobar fallback a preferencia/Checkout Pro antes de vender recurrencia real.
- Produccion no debe declararse cerrada hasta validar webhook real firmado con pago controlado.

## Siguiente paso recomendado

Configurar variables Mercado Pago en Vercel sin imprimir secretos, registrar webhook productivo en Mercado Pago Developers y ejecutar prueba controlada de bajo monto o entorno test autorizado antes de avanzar a SUNAT auxiliar/piloto.
