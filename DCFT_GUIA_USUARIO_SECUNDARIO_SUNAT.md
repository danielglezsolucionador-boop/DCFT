# DCFT Guia de Usuario Secundario SUNAT

Fecha: 2026-06-06

## Fuentes oficiales revisadas

- SUNAT Orientacion: https://orientacion.sunat.gob.pe/07-creacion-de-usuario-secundarios-de-la-clave-sol
- Gob.pe / SUNAT: https://www.gob.pe/7893-dar-acceso-a-otros-usuarios-a-tu-clave-sol
- PDF SUNAT Empresas - Crear o dar de baja usuario secundario: https://orientacion.sunat.gob.pe/sites/default/files/inline-files/IM_009_Usuario%20Secundario.pdf

## Que es un usuario secundario SUNAT

Es una autorizacion creada por el titular de la Clave SOL para que otra persona o sistema acceda a opciones especificas de consultas o tramites en SUNAT Operaciones en Linea.

La autorizacion esta bajo control del titular y puede crearse, suspenderse o eliminarse.

## Regla DCFT

DCFT solo acepta usuario secundario SUNAT para empresas.

DCFT no debe pedir ni recibir la Clave SOL principal.

Con el vault cifrado activo, DCFT puede recibir credenciales de usuario secundario SUNAT solo para consulta y guardarlas cifradas. El conector real sigue apagado hasta aprobacion CEO.

## Consentimiento requerido

Texto operativo:

> Autorizo a DCFT a usar un usuario secundario SUNAT exclusivamente para consulta y diagnostico. DCFT no declara, no paga, no emite comprobantes ni modifica informacion.

## Como crear usuario secundario

Resumen de flujo segun la documentacion oficial:

1. Ingresar a SUNAT Operaciones en Linea con la Clave SOL principal del titular.
2. Entrar a Administracion de usuarios secundarios.
3. Crear usuario.
4. Ingresar datos del usuario secundario.
5. Crear usuario y clave secundaria.
6. Asignar perfiles u opciones permitidas.
7. Quitar permisos no necesarios.
8. Verificar perfiles autorizados.
9. Grabar.

## Permisos permitidos para piloto DCFT

Permitido solo si existe como opcion de consulta:

- ficha RUC;
- estado del contribuyente;
- condicion del contribuyente;
- obligaciones o alertas visibles en modo consulta;
- informacion tributaria de lectura necesaria para diagnostico;
- comprobantes, compras o ventas solo si la opcion es lectura y el CEO la aprueba.

## Permisos no permitidos

No asignar:

- presentar declaraciones;
- enviar formularios;
- realizar pagos;
- emitir comprobantes;
- anular o dar de baja comprobantes;
- modificar datos del contribuyente;
- cambiar clave;
- administrar usuarios;
- tramites de representacion;
- acciones de cobranza, fraccionamiento o procedimientos que impliquen solicitud o escritura.

## Como revocar o desconectar

En SUNAT:

1. Ingresar a Administracion de usuarios secundarios.
2. Buscar el usuario secundario creado para DCFT.
3. Suspenderlo, eliminarlo o modificar sus permisos.

En DCFT:

1. Entrar al panel SUNAT seguro.
2. Usar desconectar SUNAT cuando este disponible.
3. Confirmar que el estado quede deshabilitado/desconectado.

## Que puede hacer DCFT en este estado

- Preparar el usuario secundario.
- Registrar consentimiento.
- Guardar usuario secundario y clave secundaria cifrados si `DCFT_CREDENTIAL_ENCRYPTION_KEY` esta configurada.
- Mostrar solo el usuario enmascarado al frontend.
- Marcar `read_only=true`.
- Marcar `remote_actions_enabled=false`.
- Generar diagnostico con datos ingresados manualmente o semi-reales autorizados.
- Informar que la conexion real esta pendiente.

## Que no puede hacer DCFT todavia

- Abrir sesion SUNAT real.
- Validar credenciales reales.
- Leer informacion privada SUNAT real.
- Ejecutar sync real.
- Declarar, pagar, emitir o modificar informacion.

## Pendiente antes de SUNAT real

- Validacion productiva con datos dummy del vault cifrado.
- Rotacion y eliminacion de credencial.
- Conector read-only aprobado por CEO.
- Validacion con empresa piloto autorizada.
