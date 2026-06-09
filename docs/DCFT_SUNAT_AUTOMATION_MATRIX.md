# DCFT SUNAT Automation Matrix

Fecha: 2026-06-09

| módulo | información deseada | vía oficial API disponible | requiere Credenciales API SUNAT | requiere SIRE | requiere CPE | requiere usuario SOL | requiere captcha | automatizable ahora | riesgo legal/técnico | estado de prueba | próximo paso |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| Ficha RUC | Estado, condición, datos RUC | desconocido | no | no | no | sí | posible | parcial | Medio: SOL web puede bloquear | read-only web bloqueado por captcha | Seguir buscando API oficial RUC |
| CPE validez comprobantes | Estado CP, estado RUC, condición domicilio, observaciones | sí | sí | no | sí | no | no | sí | Bajo si autorizado | cliente implementado, test requiere datos CP | Probar con comprobante real autorizado |
| SIRE compras | RCE, resumen, FV0621, inconsistencias | sí | sí | sí | no | sí | no API | sí | Medio: evitar endpoints de modificación | cliente implementado mock | Probar con credenciales API + usuario secundario |
| SIRE ventas | RVIE, casillas, reportes, inconsistencias | sí | sí | sí | no | sí | no API | sí | Medio: evitar aceptar/reemplazar/eliminar | cliente implementado mock | Probar periodo real autorizado |
| declaraciones y pagos | Formularios, pagos, constancias | no comprobada | desconocido | no | no | sí | posible | no | Alto: acción sensible | no implementado | No tocar sin API oficial y aprobación CEO |
| deudas / valores pendientes | Valores, saldos, cobranza | no comprobada | no comprobado | no | no | sí | posible | no | Medio/alto: SOL web y límites | documentado como ONLY_SOL_WEB | Buscar convenio/API oficial |
| omisos | Omisiones tributarias | no comprobada | desconocido | no | no | sí | posible | no | Medio | no implementado | Investigar fuente oficial |
| infracciones | Multas, sanciones, infracciones | no comprobada | desconocido | no | no | sí | posible | no | Medio | no implementado | Investigar fuente oficial |
| expedientes | Expedientes electrónicos | no comprobada | desconocido | no | no | sí | posible | no | Alto si incluye escritos | no implementado | No presentar escritos; buscar consulta API |
| escritos | Presentación/seguimiento | no comprobada | desconocido | no | no | sí | posible | no | Alto: acción de presentación | no implementado | Bloquear escritura |
| reportes tributarios | Reporte tributario y aduanero | no comprobada | desconocido | no | no | sí | posible | no | Medio | no implementado | Buscar API oficial |
| RHE / FE | Facturas/recibos, factoring | parcial/desconocido | posiblemente | no | CPE parcial | sí/no según servicio | no API | parcial | Medio | no implementado | Investigar manuales RHE/FE |
| proveedores | OSE/PSE/terceros | sí, pero externo/tercero | depende | no | depende | depende | no | no ahora | Medio: contrato externo | solo investigado | Decisión CEO antes de integrar |
| libros electrónicos | RVIE/RCE | sí vía SIRE | sí | sí | no | sí | no API | sí | Medio | implementado mock | Probar SIRE real |
| guía remisión | GRE consultas | desconocido | desconocido | no | no | sí | posible | no | Medio | no implementado | Investigar API GRE oficial |
| planilla / T-Registro | Empleados, derechohabientes | no comprobada | desconocido | no | no | sí | posible | no | Alto por datos laborales | no implementado | No tocar ahora |
| bancos / conciliación futura | Extractos, cruce SUNAT/bancos | no SUNAT | no | no | no | no | no | no ahora | Alto: datos financieros | documentado futuro | Abrir frente separado |

## Lectura ejecutiva

Automatizable primero:

- CPE validez comprobantes.
- SIRE compras.
- SIRE ventas.

No automatizable aún por API comprobada:

- Declaraciones/pagos.
- Deudas/valores.
- Expedientes/escritos.
- T-Registro/PLAME.

Regla de DCFT:

- API oficial primero.
- SOL web read-only segundo.
- Manual solo como contingencia, no como diseño principal.
