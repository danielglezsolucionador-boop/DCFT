# DCFT Piloto Asistido con Empresa Autorizada - Checklist

Fecha: 2026-06-06

Actualizacion Paquete 3: 2026-06-08. Este checklist queda alineado al cierre local empresa MYPE/Premium + SUNAT auxiliar. Produccion no fue tocada.

## Reglas de seguridad

- No usar Clave SOL principal.
- No pedir usuario principal SUNAT.
- No activar conector SUNAT real automatico.
- No hacer declaraciones.
- No hacer pagos.
- No emitir comprobantes.
- No modificar informacion.
- No automatizar tramites.
- No exponer credenciales.
- No imprimir claves.

## Antes de iniciar

- Confirmar tester autorizado.
- Confirmar 1 estudiante real/controlado.
- Confirmar 1 empresa MYPE autorizada.
- Confirmar 1 empresa Premium o trial Premium autorizada.
- Confirmar canal de soporte durante la prueba.
- Confirmar que la empresa entiende que esta fase es asistida.
- Confirmar que se usara usuario secundario SUNAT.
- Confirmar que el usuario secundario tiene solo permisos de consulta.
- Confirmar que el RUC pertenece a la empresa autorizada.
- Confirmar que el CEO/CTO aprobo la prueba.
- Confirmar que no se pegara ninguna clave en chat, matriz, reportes ni capturas.
- Confirmar que SUNAT real automatico sigue apagado.

## Estudiante

| Paso | Resultado | Evidencia | Observaciones |
| --- | --- | --- | --- |
| Crear cuenta estudiante | Pendiente | Captura pantalla inicial | No requiere RUC |
| Login estudiante | Pendiente | Captura perfil/sesion | Usar credenciales propias del tester |
| Abrir ejercicios | Pendiente | Captura lista ejercicios | Ver Contabilidad, Finanzas y Tributacion |
| Abrir un ejercicio | Pendiente | Captura enunciado | Registrar si entiende el caso |
| Ver solucion | Pendiente | Captura solucion | Confirmar que no aparece modulo empresarial indebido |
| Logout | Pendiente | Captura salida |  |
| Login nuevamente | Pendiente | Captura sesion recuperada | Confirmar persistencia |
| Enviar feedback | Pendiente | Texto breve del tester | Claridad, utilidad, dudas |

## Empresa MYPE autorizada

| Paso | Resultado | Evidencia | Observaciones |
| --- | --- | --- | --- |
| Crear cuenta empresa | Pendiente | Captura pantalla inicial | Plan MYPE, sin pedir correo ni contraseña empresarial |
| Registrar RUC autorizado | Pendiente | Captura campo RUC | No usar RUC no autorizado |
| Ingresar usuario secundario SUNAT | Pendiente | Captura antes de guardar sin mostrar clave | Solo usuario auxiliar |
| Ingresar clave secundaria SUNAT | Pendiente | No capturar valor de clave | No usar Clave SOL principal |
| Aceptar consentimiento | Pendiente | Captura checkbox marcado | Consentimiento explicito obligatorio |
| Elegir plan y periodo | Pendiente | Captura MYPE mensual/anual | Activacion solo tras pago confirmado |
| Guardar acceso seguro | Pendiente | Captura resultado | Confirmar estado recibido |
| Confirmar que la clave desaparece | Pendiente | Captura post-guardado | Campo password vacio/no visible |
| Ver estado SUNAT auxiliar | Pendiente | Captura estado | Esperado: preparado, recibido o desconectado; no sesion real |
| Ver diagnostico pendiente/asistido | Pendiente | Captura diagnostico | Sin lectura SUNAT real automatica |
| Ver semaforo | Pendiente | Captura semaforo | Pendiente/verde/ambar/rojo segun evidencia disponible |
| Logout | Pendiente | Captura salida |  |
| Login nuevamente | Pendiente | Captura estado persistente | Confirmar vault/status persisten |
| Desconectar SUNAT si se requiere | Pendiente | Captura desconectado | Revocacion desde DCFT; usuario tambien puede revocar en SUNAT |
| Enviar feedback | Pendiente | Texto breve del tester | Claridad, confianza, fricciones |

Validacion tecnica esperada para MYPE:

- Consentimiento obligatorio antes de guardar.
- Password no vuelve al frontend.
- Username enmascarado.
- Status visible.
- Desconexion visible y funcional.
- Mensaje sin datos reales: `Esperando datos autorizados para diagnostico completo.`

## Empresa Premium autorizada o trial Premium

| Paso | Resultado | Evidencia | Observaciones |
| --- | --- | --- | --- |
| Crear cuenta empresa | Pendiente | Captura pantalla inicial | Plan Premium, sin pedir correo ni contraseña empresarial |
| Elegir plan y periodo | Pendiente | Captura Premium mensual/anual | Activacion solo tras pago confirmado |
| Registrar RUC autorizado | Pendiente | Captura campo RUC | Solo empresa autorizada |
| Ingresar usuario secundario SUNAT | Pendiente | Captura sin clave | Usuario auxiliar de consulta |
| Ingresar clave secundaria SUNAT | Pendiente | No capturar valor de clave | No usar Clave SOL principal |
| Aceptar consentimiento | Pendiente | Captura checkbox marcado | Obligatorio |
| Guardar acceso seguro | Pendiente | Captura estado | Vault activo |
| Medico de cabecera | Pendiente | Captura modulo | Confirmar visibilidad Premium |
| Diagnostico | Pendiente | Captura diagnostico | Asistido, sin conector real automatico |
| Reporte | Pendiente | Captura modulo reporte | Confirmar bloqueos si falta evidencia |
| Semaforo | Pendiente | Captura semaforo | Confirmar causa del color |
| Persistencia logout/login | Pendiente | Captura estado recuperado |  |
| Feedback | Pendiente | Texto breve del tester | Valor, claridad, confianza, precio |

Validacion tecnica esperada para Premium:

- Reportes visibles sin inventar diagnostico si falta evidencia.
- Semaforo visible con causa.
- Doctor empresa pendiente de proveedor IA y autorizacion CEO.
- Cuota comercial visible: 30 preguntas/mes.
- Status SUNAT auxiliar y desconexion disponibles.

## Cierre de cada tester

- Confirmar que no se uso Clave SOL principal.
- Confirmar que no se imprimio ninguna clave.
- Confirmar que SUNAT real automatico siguio apagado.
- Registrar bloqueos.
- Registrar decision: continuar, corregir, pausar o descartar.

## Validacion Bloque 2 SUNAT auxiliar - 2026-06-08

- Produccion backend responde con PostgreSQL persistente.
- `/sunat/auxiliary-access/requirements` reporta vault valido y almacenamiento cifrado activo en runtime.
- `/sunat/data-classification` mantiene `read_only=true`, `real_connector_enabled=false`, `real_sunat_session=false` y `remote_actions_enabled=false`.
- Tests dummy validan consentimiento obligatorio, guardado cifrado, username enmascarado, status y desconexion.
- No se uso Clave SOL principal.
- No se ejecuto sesion SUNAT real.
- Riesgo operativo: `vercel env pull --environment=production` devuelve `DCFT_CREDENTIAL_ENCRYPTION_KEY` vacia aunque el runtime desplegado la reporta valida; antes de cualquier redeploy se debe reconfigurar o confirmar esa variable.
