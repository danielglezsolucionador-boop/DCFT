# DCFT Bank Reconciliation Future

Fecha: 2026-06-09

## Propósito

La conciliación bancaria será un módulo futuro de DCFT para cruzar movimientos bancarios contra ventas, compras, comprobantes y señales SUNAT.

## Alcance futuro

- Carga mensual de extractos bancarios.
- Normalización de movimientos.
- Cruce contra ventas registradas.
- Cruce contra compras registradas.
- Comparación con información SUNAT disponible por CPE/SIRE.
- Detección de ingresos no declarados.
- Detección de pagos no sustentados.
- Señales de riesgo IGV/renta.
- Recomendaciones contables y tributarias.

## No implementado ahora

- No se conectan bancos.
- No se solicitan claves bancarias.
- No se abren APIs bancarias.
- No se procesan extractos reales.
- No se mezcla con Mercado Pago ni Stripe.

## Relación con diagnóstico tributario

Cuando SIRE/CPE estén funcionando, la conciliación bancaria podrá usar esos hechos normalizados como base tributaria. El motor deberá comparar:

- Ingresos bancarios vs ventas SUNAT/SIRE.
- Egresos bancarios vs compras SUNAT/SIRE.
- Comprobantes observados vs movimientos asociados.
- Periodos con diferencias relevantes.

## Condición de apertura

Este frente solo debe abrirse con autorización CEO específica y reglas de protección de datos financieros.
