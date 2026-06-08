# Guia para Empresa Piloto - DCFT y SUNAT Auxiliar

Fecha: 2026-06-06

Actualizacion Paquete 3: 2026-06-08. Guia vigente para piloto asistido local; no implica push, deploy ni activacion de SUNAT real automatico.

## 1. Que es DCFT

DCFT es el Doctor Contable Financiero Tributario. Ayuda a revisar la salud contable, financiera y tributaria de una empresa, mostrar alertas, ordenar evidencias y preparar diagnosticos entendibles para tomar mejores decisiones.

## 2. Que se probara

En este piloto asistido se probara:

- Creacion de cuenta empresa.
- Registro de RUC autorizado.
- Uso de usuario secundario SUNAT.
- Consentimiento explicito.
- Guardado seguro del acceso auxiliar.
- Estado del vault SUNAT auxiliar.
- Diagnostico y semaforo inicial.
- Persistencia al cerrar sesion y volver a entrar.
- Desconexion del acceso auxiliar si se requiere.

## 3. Que es un usuario secundario SUNAT

Es un usuario auxiliar creado por la empresa en SUNAT para dar acceso limitado. Debe tener permisos minimos de consulta. No debe ser el usuario principal ni la Clave SOL principal de la empresa.

## 4. Por que no usar Clave SOL principal

La Clave SOL principal puede permitir acciones sensibles. En este piloto no queremos que DCFT tenga capacidad de declarar, pagar, emitir comprobantes, modificar datos ni realizar tramites. Usar usuario secundario reduce riesgo y permite revocar permisos.

## 5. Texto obligatorio de seguridad

"En esta prueba, DCFT no declara, no paga, no emite comprobantes y no modifica información. El usuario secundario SUNAT se usará solo para preparar el flujo seguro de consulta y diagnóstico."

## 6. Que puede hacer DCFT ahora

- Crear y mantener una cuenta empresa.
- Registrar RUC autorizado.
- Recibir consentimiento explicito.
- Guardar el acceso auxiliar en vault cifrado.
- Mostrar usuario SUNAT enmascarado.
- Mostrar estado del acceso auxiliar.
- Preparar diagnostico asistido con informacion disponible.
- Mostrar semaforo y proximos pasos.
- Permitir desconexion del acceso auxiliar.

## 7. Que NO puede hacer DCFT ahora

- No declara impuestos.
- No paga impuestos.
- No emite comprobantes.
- No modifica datos.
- No cambia informacion de SUNAT.
- No automatiza tramites.
- No abre una sesion SUNAT real automatica.
- No debe recibir Clave SOL principal.

## 8. Estado de SUNAT real automatico

En esta fase SUNAT real automatico sigue apagado. El conector read-only real todavia no se activa. La prueba es asistida y controlada.

## 9. Seguridad del acceso

- La clave secundaria se envia solo al endpoint seguro del vault.
- La clave se guarda cifrada si el vault esta activo.
- La clave no se muestra despues de guardarse.
- El usuario SUNAT se muestra enmascarado.
- El usuario puede desconectar el acceso desde DCFT.
- La empresa tambien debe poder revocar o ajustar permisos desde SUNAT.

## 10. Capturas que debe enviar el tester

No enviar capturas que muestren claves.

Enviar capturas de:

- Pantalla de cuenta creada.
- RUC registrado.
- Consentimiento aceptado.
- Estado SUNAT auxiliar luego de guardar.
- Campo de clave vacio/no visible despues de guardar.
- Diagnostico o semaforo.
- Reporte o medico de cabecera si aplica.
- Pantalla posterior a logout/login.
- Desconexion si se ejecuta.

## 11. Feedback esperado

Responder:

- Que fue claro.
- Que genero duda.
- Que dio confianza.
- Que dio desconfianza.
- Que pantalla fue dificil.
- Que decision tomaria con el diagnostico.
- Que esperaria que haga DCFT en la siguiente version.

## 12. Cierre del piloto

El piloto queda valido si la empresa confirma:

- Se uso RUC autorizado.
- Se uso usuario secundario SUNAT.
- No se uso Clave SOL principal.
- Se acepto consentimiento.
- La clave no volvio a mostrarse.
- DCFT no ejecuto acciones reales en SUNAT.
- El diagnostico/semaforo fue entendible.

## 13. Estado local Paquete 3

- Entrada empresa mobile 390x844 validada localmente.
- RUC, razon social, correo, contrasena, usuario secundario SUNAT, clave secundaria SUNAT, consentimiento, MYPE, Premium, `Crear cuenta empresa`, `Entrar como empresa` y `Ver seguridad` quedan visibles.
- DCFT muestra: `Usa un usuario secundario SUNAT. No uses tu Clave SOL principal.`
- DCFT muestra: `DCFT no declara, no paga, no emite comprobantes y no modifica informacion.`
- DCFT muestra: `El acceso se guarda cifrado.`
- DCFT muestra: `SUNAT real automatico sigue apagado hasta autorizacion.`
- Doctor empresa se mantiene pendiente de proveedor IA y autorizacion CEO.
- MYPE: 10 preguntas/mes cuando se active Doctor empresa.
- Premium: 30 preguntas/mes cuando se active Doctor empresa.

## 14. Que no debe hacerse en el piloto

- No pegar claves en chat.
- No poner claves en matriz.
- No capturar pantallas con claves visibles.
- No usar Clave SOL principal.
- No pedir permisos de declaracion, pago, emision o modificacion.
- No activar SUNAT real automatico.
- No declarar, no pagar, no emitir comprobantes y no modificar informacion.
