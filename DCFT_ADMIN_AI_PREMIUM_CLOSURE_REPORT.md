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

## Producción final

- Backend desplegado y aliasado a `https://dcft.vercel.app`.
- Frontend desplegado y aliasado a `https://dcft-frontend.vercel.app`.
- `GET https://dcft.vercel.app/health`: PASS (`status=ok`).
- Frontend: PASS (`HTTP 200`).
- Admin/CEO login: PASS.
- Identidad Admin: rol `ceo`, plan `internal`, suscripción `active`.
- Premium Admin: PASS (`premium=true`).
- Pago Admin: no requerido (`payment_required=false`, `payment_status=not_required`).
- Checkout Admin: bloqueado correctamente con HTTP 403.
- Acceso SUNAT Admin: PASS mediante consulta autenticada de estado, sin usar ni exponer credenciales SOL reales.
- IA mínima: PASS; proveedor `openrouter` no configurado y respuesta controlada disponible.
- Bundle frontend: contiene RUC, Usuario SOL y Clave SOL; no contiene usuario secundario, clave secundaria ni SUNAT auxiliar.
- Cliente empresa/pago: protegido por tests backend; no se ejecutó un cobro real de producción.

## Seguridad

- No se imprimieron secretos.
- No se agregaron `.env`.
- La contraseña Admin de producción se rotó a una credencial fuerte y quedó guardada solo en el `.env` excluido y en Vercel como variable sensible.
- No se registran claves SOL completas.
- No se agregó bypass público tipo `?admin=true`; el parámetro de frontend solo muestra formulario de login admin y no concede privilegios.
