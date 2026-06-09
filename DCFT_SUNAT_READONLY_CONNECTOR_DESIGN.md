# DCFT SUNAT Read-Only Connector - Diseno

Fecha: 2026-06-06

Estado: Diseno solamente. No implementado. No activado.

## 1. Que intentaria hacer el conector

El conector read-only intentaria abrir un flujo de consulta controlado con usuario secundario SUNAT para leer informacion minima autorizada y alimentar un diagnostico contable, financiero y tributario.

Objetivo limitado:

- Confirmar que el usuario secundario puede consultar informacion autorizada.
- Leer solo datos necesarios para diagnostico.
- Registrar evidencias de lectura.
- Mostrar riesgos y proximos pasos en lenguaje humano.

## 2. Como validaria usuario secundario

- Exigir RUC autorizado.
- Exigir consentimiento explicito.
- Exigir usuario secundario SUNAT.
- Rechazar Clave SOL principal.
- Verificar que el vault esta configurado y valido.
- Verificar que `read_only=true`.
- Verificar que `remote_actions_enabled=false`.
- Verificar aprobacion CEO antes de iniciar cualquier sesion real.

## 3. Informacion minima a leer

La primera version deberia limitarse a informacion de consulta, por ejemplo:

- Ficha RUC y estado/condicion si esta disponible.
- Obligaciones o alertas visibles de consulta si estan disponibles.
- Metadatos basicos necesarios para diagnostico.
- Evidencia de acceso y fecha de revision.

No debe leer informacion innecesaria ni masiva en la primera fase.

## 4. Que NO haria

- No declarar.
- No pagar.
- No emitir comprobantes.
- No modificar informacion.
- No presentar formularios.
- No firmar documentos.
- No administrar usuarios.
- No cambiar claves.
- No automatizar tramites.
- No operar con Clave SOL principal.

## 5. Manejo de errores

Errores esperados:

- Credencial incorrecta.
- Usuario secundario sin permisos suficientes.
- RUC no coincide con empresa autorizada.
- Sesion vencida.
- SUNAT no disponible.
- Captcha.
- 2FA.
- Bloqueo o alerta de seguridad SUNAT.

Respuesta esperada:

- Mostrar estado humano.
- No reintentar agresivamente.
- No bloquear la cuenta.
- Registrar auditoria sanitizada.
- No imprimir claves ni tokens.
- Pedir accion manual al tester/CEO.

## 6. Captcha

Si aparece captcha:

- Detener automatizacion.
- Mostrar estado `requiere_intervencion_humana`.
- No intentar resolver captcha automaticamente en esta fase.
- Documentar captura sin datos sensibles.

## 7. 2FA

Si aparece 2FA:

- Detener automatizacion.
- No pedir codigos por chat.
- Solicitar proceso asistido con el titular.
- Evaluar si el piloto debe seguir manual o pausarse.

## 8. Bloqueo de sesion SUNAT

Si SUNAT bloquea la sesion:

- Detener conector.
- Marcar riesgo critico.
- No reintentar.
- Informar al CEO/CTO.
- Pedir a la empresa revisar estado del usuario auxiliar.

## 9. Riesgos

- SUNAT puede cambiar interfaz o reglas.
- Browser automation puede ser fragil.
- Permisos mal configurados pueden exponer mas informacion de la necesaria.
- Intentos repetidos pueden bloquear usuario.
- El usuario auxiliar sigue siendo responsabilidad de la empresa.
- El alcance legal/tributario debe mantenerse como diagnostico, no ejecucion.

## 10. Browser automation vs piloto manual/asistido

Recomendacion actual: piloto manual/asistido primero.

Motivos:

- Menor riesgo de bloqueo.
- Mejor aprendizaje sobre pantallas reales.
- Permite confirmar permisos necesarios.
- Evita automatizar antes de entender variaciones de SUNAT.

Browser automation solo deberia evaluarse despues de:

- 2 o 3 pilotos asistidos exitosos.
- Permisos minimos confirmados.
- Aprobacion CEO/CTO.
- Plan de manejo de captcha/2FA.
- Auditoria y observabilidad preparadas.

## 11. Aprobacion CEO requerida

Antes de activar cualquier conector real:

- Aprobar alcance exacto de lectura.
- Aprobar lista de RUCs autorizados.
- Aprobar usuario secundario y permisos minimos.
- Aprobar manejo de errores, captcha y 2FA.
- Aprobar politica de reintentos.
- Aprobar reporte de riesgos.
- Confirmar que SUNAT real automatico puede pasar de apagado a piloto read-only.

Sin esa aprobacion, `real_connector_enabled=false` debe mantenerse.

## 12. Estado tecnico Paquete 3 - 2026-06-08

- Este documento sigue siendo diseno/control futuro.
- Paquete 3 no activa conector SUNAT real.
- Paquete 3 valida solo flujo empresa, consentimiento y vault SUNAT auxiliar local.
- Flags que deben mantenerse:
  - `real_connector_enabled=false`.
  - `real_sunat_session=false`.
  - `remote_actions_enabled=false`.
  - `read_only=true`.
- Endpoints de vault cubiertos por tests:
  - `POST /sunat/auxiliary/credentials`.
  - `GET /sunat/auxiliary/status`.
  - `DELETE /sunat/auxiliary/credentials`.
- El Doctor empresa no debe usar datos SUNAT reales ni diagnostico automatico hasta proveedor IA configurado y autorizacion CEO/CTO.
- El piloto asistido debe usar usuario secundario SUNAT y consentimiento explicito, nunca Clave SOL principal.

## 13. Validacion Bloque 2 SUNAT auxiliar - 2026-06-08

- Produccion mantiene PostgreSQL persistente y SQLite apagado.
- El runtime publico declara que no hay acciones autonomas SUNAT, bancarias ni legales.
- `/sunat/auxiliary-access/requirements` reporta vault configurado y valido en runtime.
- `/sunat/data-classification` confirma `read_only=true`, `real_connector_enabled=false`, `real_sunat_session=false` y `remote_actions_enabled=false`.
- Tests dummy validan endpoints de credenciales auxiliares, consentimiento, cifrado, mascara, status, aislamiento tenant y desconexion.
- No se activo conector real.
- No se abrio sesion SUNAT real.
- No se usaron credenciales reales.
- Riesgo antes de redeploy: `DCFT_CREDENTIAL_ENCRYPTION_KEY` debe revalidarse en Vercel Production porque el runtime desplegado esta sano, pero `env pull` devuelve la variable vacia.
