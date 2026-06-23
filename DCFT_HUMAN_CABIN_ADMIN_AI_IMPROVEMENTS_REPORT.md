# DCFT Human Cabin Admin AI Improvements Report

Fecha: 2026-06-22

## Resumen

Se mejoro Cabina Humana DCFT para la fase Admin CEO / semaforo / Doctor Contable / Auditoria Interna / IA configurable sin crear proyecto nuevo, sin tocar CENTINELA, HERMES, FORJA, CEREBRO, SOMBRA ni Hetzner, y sin modificar Mercado Pago fuera de verificaciones de acceso.

## Backup

Backup previo valido usado como referencia de cierre: `D:\ECOSYSTEM\BACKUPS\dcft-before-human-cabin-improvements-20260620-020419.zip`.

No se genero backup nuevo.

## Cambios backend

- `CurrentUser` ahora expone `access_level`.
- Admin CEO/internal queda con `premium=true`, `payment_required=false`, `internal=true`, `access_level=full`.
- Cliente empresa normal solo obtiene premium si la suscripcion comercial esta activa.
- `/dashboard/summary` recibe rol del usuario para no perder contexto interno CEO.
- `/subscriptions/status` y `/subscriptions/checkout/status` exponen `access_level`.
- Doctor Contable IA mantiene fallback exacto `Proveedor IA no configurado` si no hay proveedor/key.
- Si el proveedor IA responde, la respuesta se normaliza a estructura minima:
  1. Diagnostico breve
  2. Riesgo tributario/contable
  3. Accion recomendada
  4. Documentos necesarios
  5. Proximo paso
  6. Advertencia

## Cambios frontend

- Banda visible: `Modo Admin CEO activo`, `Plan interno`, `Premium habilitado`, `No requiere pago`.
- Acceso premium visual desbloqueado para Admin CEO sin CTA obligatorio de Mercado Pago.
- Doctor Contable disponible para Admin CEO y cuentas con premium confirmado.
- Auditoria Interna agregada como panel operativo.
- Semaforo ampliado a: general, tributario, financiero, contable, SOL/conexion segura, documentos/evidencias y recomendaciones.
- Cliente empresa sin pago conserva bloqueo premium.
- Documentos/evidencias ya no queda vacio: muestra cargados, faltantes, pendientes, sensibles bloqueados, integridad y siguiente paso.
- Alertas/recomendaciones muestran nivel, area, explicacion, recomendacion y accion cuando aplica.

## Cabina Corazon / perfil encontrado

- No se encontro archivo exacto de Cabina Corazon DCFT.
- Reportes existentes confirmados: `DCFT_HEART_CABIN_DISCOVERY_REPORT.md` y `DCFT_CABINAS_ORIGINALES_DISCOVERY_REPORT.md`.
- Criterios aplicados:
  - No inventar datos tributarios reales.
  - Mantener SUNAT read-only/controlado.
  - Mostrar causa del semaforo para no confundir falta de datos con bug.
  - Separar diagnostico de ejecucion oficial.

## IA Provider

- Variables esperadas: `DCFT_AI_PROVIDER`, `DCFT_AI_API_KEY`.
- Proveedor preferente: `openrouter`.
- Si no hay API key, Doctor Contable responde controlado: `Proveedor IA no configurado`.
- No se imprimio ni guardo API key.
- Arquitectura queda preparada para futuro `DCFT_AI_PROVIDER=cerebro`, sin conectar Cerebro en esta fase.

## QA local

- `.venv\Scripts\python.exe -m compileall . -q`: PASS.
- `.venv\Scripts\python.exe -m pytest apps\backend\tests\test_operational_backend.py -q`: PASS, 80 passed.
- `npm run build` en `apps/frontend`: PASS.
- `git diff --check`: PASS con advertencias CRLF normales.
- Secret scan de diff: PASS, sin secretos reales detectados.

## Produccion

- Backend health inicial confirmado OK en `https://dcft.vercel.app/health`.
- Validacion final de produccion queda sujeta a deploy y login CEO con password definido por CEO.

## Riesgos y bloqueos

- Si `DCFT_AI_API_KEY` no esta configurada en Vercel Production, IA queda en fallback controlado.
- No se puede validar login real Admin CEO en produccion sin conocer el password CEO.
- Mercado Pago se mantiene intacto; pruebas existentes cubren pendiente, aprobado, rechazado y no activacion prematura.

## Siguiente paso

Commit, push a `origin/main`, deploy existente y validacion visual/produccion.
