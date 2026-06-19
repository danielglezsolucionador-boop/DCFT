# DCFT Admin CEO / IA mínima / Premium closure

Fecha: 2026-06-18

## Alcance

- Repo real: `C:\Users\admin\dcft-knowledge-core`
- Backend producción esperado: `https://dcft.vercel.app`
- Frontend producción esperado: `https://dcft-frontend.vercel.app`
- No se tocaron CENTINELA, HERMES, FORJA, CEREBRO, SOMBRA ni Hetzner.

## Backup

- Backup pre-cambio: `D:\ECOSYSTEM\BACKUPS\dcft-admin-ceo-ai-premium-prechange-20260618-184413.zip`
- Entradas verificadas: 5,747
- Entradas prohibidas detectadas: 0
- SHA256: `2D3067A8EEB28A68F218A76B77C380EE7695B7F652D8C89D657F28E5892A085F`

## Implementación

- Admin/CEO interno queda con rol `ceo`, plan `internal`, `premium=true`, `payment_required=false`.
- El usuario interno configurado por entorno no requiere Mercado Pago y no puede ser enviado a checkout.
- Los planes comerciales de clientes (`mype`, `premium`) quedan protegidos: cliente normal no puede autoupgradearse por API; requiere checkout/webhook aprobado o acción Admin CEO.
- Mercado Pago queda reservado para clientes empresa y renovaciones comerciales.
- Flujo empresa/SOL mantiene RUC, Usuario SOL, Clave SOL y consentimiento.
- IA mínima agregada en `/ai/tax/ask`.
- Si no hay proveedor/key configurado, responde controladamente: `Proveedor IA no configurado`.
- Variable genérica soportada: `DCFT_AI_PROVIDER` + `DCFT_AI_API_KEY`.
- No se añadió ninguna API key al código ni al reporte.

## QA local final

- `python -m compileall . -q`: PASS
- `python -m pytest -q`: PASS, 73 tests
- `git diff --check`: PASS
- secret scan sobre diff: PASS
- `npm run build`: PASS

## Producción pendiente/final

Validar después de deploy:

- `GET https://dcft.vercel.app/health`
- `https://dcft-frontend.vercel.app`
- Admin/CEO login sin pago
- Admin/CEO premium operativo
- Cliente empresa con pago requerido
- IA configurable o respuesta controlada sin key

## Seguridad

- No se imprimieron secretos.
- No se agregaron `.env`.
- No se registran claves SOL completas.
- No se agregó bypass público tipo `?admin=true`; el parámetro de frontend solo muestra formulario de login admin y no concede privilegios.
