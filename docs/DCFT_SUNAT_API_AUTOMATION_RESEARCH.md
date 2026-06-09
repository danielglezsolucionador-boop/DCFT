# DCFT SUNAT API Automation Research

Fecha de investigación: 2026-06-09

## Objetivo

No abandonar la automatización SUNAT por el bloqueo de captcha del flujo web SOL. DCFT debe priorizar rutas oficiales API cuando existan, sin romper captcha, sin evadir seguridad y sin fingir éxito.

## Fuentes oficiales revisadas

- SUNAT CPE, Manual de Consulta Integrada de Comprobante de Pago por Servicio Web: https://cpe.sunat.gob.pe/sites/default/files/inline-files/Manual-de-Consulta-Integrada-de-Comprobante-de-Pago-por-ServicioWEB_v2_0.pdf
- SUNAT CPE, Consultas de CPE: https://cpe.sunat.gob.pe/consultas-de-cpe
- SUNAT CPE, Servicios Web disponibles: https://cpe.sunat.gob.pe/sites/default/files/2026-05/Descarga%20aqu%C3%AD%20los%20Servicios%20WEB%20Disponibles%20-%20Incluye%20DDJJ%20de%20Boletos%20a%C3%A9reos.pdf
- SUNAT SIRE, portal oficial: https://sire.sunat.gob.pe/
- SUNAT orientación SIRE: https://orientacion.sunat.gob.pe/05-registros-electronicos-sire
- SUNAT CPE, Formas de acceso al SIRE: https://cpe.sunat.gob.pe/node/158
- SUNAT CPE, RVIE: https://cpe.sunat.gob.pe/node/129
- SUNAT CPE, RCE: https://cpe.sunat.gob.pe/node/130
- SUNAT SIRE Compras API manual v26.0: https://cpe.sunat.gob.pe/sites/default/files/inline-files/Manual%20de%20servicios%20Web%20Api%20-%20SIRE_Compras%20v26_0.pdf
- SUNAT SIRE Ventas API manual v27: https://cpe.sunat.gob.pe/sites/default/files/inline-files/Manual%20de%20servicios%20Web%20Api%20-%20SIRE_Ventas%20v27.pdf
- SUNAT orientación Mis Declaraciones y Pagos: https://orientacion.sunat.gob.pe/a-mis-declaraciones-y-pagos-declara-facil
- SUNAT orientación deuda en cobranza coactiva: https://orientacion.sunat.gob.pe/2913-consulta-deuda-en-cobranza-coactiva-personas
- SUNAT orientación escritos electrónicos: https://orientacion.sunat.gob.pe/presentacion-de-escritos-electronicos-1

## 1. Credenciales de API SUNAT

Ruta oficial identificada:

- SOL -> Empresas -> Comprobantes de pago -> Consulta de Validez de Comprobantes de Pago -> Credenciales de API SUNAT.
- Para SIRE, SUNAT indica que se debe ingresar a SUNAT Operaciones en Línea y obtener las credenciales que habilitan el servicio web API SUNAT.

Qué devuelve:

- `client_id`, llamado también Id en pantallas/manuales.
- `client_secret`, llamado también Clave.

Uso confirmado:

- Consulta integrada de validez CPE.
- Servicio Web API SUNAT para SIRE RVIE/RCE.

Notas:

- En CPE se usa `grant_type=client_credentials`.
- En SIRE se usa `grant_type=password` con Credenciales API SUNAT y credenciales SOL del generador.
- Para DCFT, estas credenciales se guardan cifradas y no se devuelven al frontend.
- El permiso "Credenciales de API SUNAT" queda separado como permiso de automatización API, no como autorización para declarar, pagar o modificar.

## 2. Consulta Integrada de Validez de Comprobantes por Servicio Web

Endpoint oficial documentado:

- Token: `https://api-seguridad.sunat.gob.pe/v1/clientesextranet/{client_id}/oauth2/token/`
- Servicio: `https://api.sunat.gob.pe/v1/contribuyente/contribuyentes/{RUC}/validarcomprobante`

Autenticación:

- `grant_type=client_credentials`
- `scope=https://api.sunat.gob.pe/v1/contribuyente/contribuyentes`
- `client_id`
- `client_secret`
- Header de consulta: `Authorization: Bearer <token>`

Payload mínimo:

- `numRuc`
- `codComp`
- `numeroSerie`
- `numero`
- `fechaEmision`
- `monto` para comprobantes electrónicos cuando aplique

Respuesta útil para DCFT:

- Estado del comprobante.
- Estado del RUC.
- Condición de domicilio.
- Observaciones.

Estado DCFT:

- Implementado como cliente CPE oficial.
- Requiere datos de comprobante de prueba para validación real.
- Sin datos de comprobante, responde `TEST_DATA_REQUIRED`.

## 3. SIRE Ventas API

Fuente:

- Manual de servicios Web API - SIRE Ventas v27.

Autenticación:

- Token SUNAT por `https://api-seguridad.sunat.gob.pe/v1/clientessol/{client_id}/oauth2/token/`
- `grant_type=password`
- `scope=https://api-sire.sunat.gob.pe`
- `client_id`
- `client_secret`
- `username={RUC}{USUARIO}`
- `password={CLAVESOL}`

Endpoints oficiales de lectura identificados:

- Reporte de casillas propuestas RVIE.
- Descarga de inconsistencias.
- Descarga de registros/archivos vía ticket.
- Reportes de exportadores.

Restricción DCFT:

- DCFT solo implementa sync de lectura.
- No implementa aceptar propuesta, reemplazar propuesta, registrar preliminar, excluir comprobantes ni eliminar preliminares.

Estado DCFT:

- Cliente SIRE Ventas creado.
- Endpoint backend: `POST /sunat/api/sire/sales/sync`.
- Requiere Credenciales API SUNAT y usuario secundario SOL cifrado.

## 4. SIRE Compras API

Fuente:

- Manual de servicios Web API - SIRE Compras v26.0.

Autenticación:

- Igual que SIRE Ventas: Credenciales API SUNAT + usuario/clave SOL del generador.

Endpoints oficiales de lectura identificados:

- Consulta FV0621 para RCE.
- Descarga de resumen de comprobantes RCE.
- Consulta estado de ticket.
- Descarga de archivo ticket.
- Descarga de inconsistencias.
- Consulta preliminares registrados.

Restricción DCFT:

- DCFT solo implementa lectura/sync.
- No implementa grabar crédito fiscal, aceptar, reemplazar, eliminar ni registrar preliminares.

Estado DCFT:

- Cliente SIRE Compras creado.
- Endpoint backend: `POST /sunat/api/sire/purchases/sync`.
- Requiere Credenciales API SUNAT y usuario secundario SOL cifrado.

## 5. Reportes tributarios / declaraciones / pagos

Resultado:

- Se encontró documentación oficial de plataforma SOL / Mis Declaraciones y Pagos.
- No se confirmó API REST oficial pública para que DCFT consulte o presente declaraciones/pagos de forma automática.

Decisión DCFT:

- No implementar declaraciones ni pagos.
- Estado técnico: `ONLY_SOL_WEB`.
- Seguir investigando solo si SUNAT publica API oficial o convenio autorizado.

## 6. T-Registro / PLAME / planilla

Resultado:

- No se confirmó API oficial pública para automatización DCFT.
- PLAME y planilla siguen asociados a plataformas/aplicativos oficiales.

Decisión DCFT:

- No implementar ahora.
- Estado técnico: `ONLY_SOL_WEB` o `UNKNOWN_OFFICIAL_API`.

## 7. Deudas / cobranza / valores pendientes

Resultado:

- SUNAT orienta a consultar valores pendientes desde SOL.
- Se identificó pantalla web de consulta de valores, con límites y flujo de reporte.
- No se confirmó API oficial pública para DCFT.

Decisión DCFT:

- No automatizar por scraping ni captcha.
- Estado técnico: `ONLY_SOL_WEB`.

## 8. Expedientes / escritos / omisos / infracciones

Resultado:

- Escritos electrónicos aparecen documentados como flujo SOL.
- No se confirmó API oficial pública para DCFT.
- Infracciones se apoyan en Código Tributario y sistemas de consulta, no en API comprobada para DCFT.

Decisión DCFT:

- No implementar escritura ni presentación.
- Lectura automática queda pendiente de fuente oficial comprobada.

## 9. Proveedores autorizados o terceros

Opciones investigadas:

- PSE/OSE para comprobantes y facturación electrónica.
- Servicios privados de facturación o contabilidad con API.

Decisión DCFT:

- No integrar terceros sin decisión CEO.
- No pagar ni registrar proveedores externos.
- Documentar como alternativa secundaria, no como ruta principal.

## Conclusión técnica

Sí hay rutas oficiales API relevantes:

- CPE validez comprobantes.
- SIRE Ventas.
- SIRE Compras.

No hay ruta oficial API comprobada en este bloque para:

- Declaraciones/pagos.
- Deudas/valores.
- Expedientes/escritos.
- T-Registro/PLAME.

La estrategia correcta es:

1. Mantener el read-only web SOL como capa secundaria bloqueable por captcha.
2. Priorizar Credenciales API SUNAT para CPE/SIRE.
3. Guardar evidencia raw y normalizada.
4. No pasar a descarga manual como primera solución.
5. Reportar límites oficiales sin fingir éxito.
