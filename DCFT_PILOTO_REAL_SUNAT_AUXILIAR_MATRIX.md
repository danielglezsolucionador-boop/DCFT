# DCFT Piloto Real Controlado con SUNAT Auxiliar - Matriz

Fecha: 2026-06-06

## Regla CEO

Las empresas del piloto DCFT deben usar usuario secundario SUNAT si o si.

No se acepta Clave SOL principal. No se piden accesos principales. No se declaran impuestos, no se pagan impuestos, no se emiten comprobantes y no se modifica informacion SUNAT.

## Tester 1 - Estudiante

- Tipo: estudiante.
- RUC: no requerido.
- SUNAT auxiliar: no requerido.
- Plan: student.
- Flujo:
  - crear cuenta estudiante;
  - login;
  - revisar ejercicios;
  - revisar primeros pasos;
  - enviar feedback.
- Criterio PASS:
  - login funciona;
  - ejercicios visibles;
  - no se solicita RUC;
  - no se solicita SUNAT auxiliar;
  - feedback recibido.

## Tester 2 - Empresa MYPE

- Tipo: empresa MYPE.
- RUC: real autorizado o RUC de prueba autorizado por el CEO.
- SUNAT auxiliar: obligatorio.
- Clave SOL principal: prohibida.
- Plan: mype.
- Flujo:
  - crear cuenta empresa;
  - registrar RUC y razon social;
  - crear usuario secundario SUNAT externo a DCFT siguiendo guia;
  - ingresar usuario secundario y clave secundaria en DCFT solo con vault cifrado activo;
  - aceptar consentimiento read-only;
  - guardar acceso seguro y confirmar usuario enmascarado;
  - revisar estado SUNAT;
  - generar diagnostico inicial con datos disponibles o semi-reales autorizados;
  - revisar semaforo tributario/contable/financiero.
- Criterio PASS:
  - SUNAT auxiliar guardado en vault cifrado;
  - `read_only=true`;
  - `remote_actions_enabled=false`;
  - `real_connector_enabled=false` hasta aprobacion tecnica;
  - diagnostico no inventa datos si SUNAT real no esta conectado;
  - feedback recibido.

## Tester 3 - Empresa Premium

- Tipo: empresa Premium.
- RUC: real autorizado o RUC de prueba autorizado por el CEO.
- SUNAT auxiliar: obligatorio.
- Clave SOL principal: prohibida.
- Plan: premium.
- Trial: Premium 7 dias.
- Flujo:
  - crear cuenta empresa;
  - registrar RUC y razon social;
  - crear usuario secundario SUNAT externo a DCFT siguiendo guia;
  - ingresar usuario secundario y clave secundaria en DCFT solo con vault cifrado activo;
  - aceptar consentimiento read-only;
  - guardar acceso seguro y confirmar usuario enmascarado;
  - activar/confirmar trial Premium 7 dias;
  - revisar medico de cabecera;
  - generar diagnostico inicial;
  - revisar semaforo;
  - generar reporte inicial;
  - enviar feedback.
- Criterio PASS:
  - SUNAT auxiliar guardado en vault cifrado;
  - trial Premium 7 dias activo;
  - medico de cabecera visible;
  - reporte inicial generado con datos disponibles o semi-reales autorizados;
  - no se usan credenciales principales;
  - no se ejecutan acciones remotas.

## Datos que debe entregar el CEO antes del piloto

- Correo de tester estudiante.
- Correo de tester empresa MYPE.
- Correo de tester empresa Premium.
- RUC autorizado para MYPE.
- RUC autorizado para Premium.
- Confirmacion de que cada empresa creo usuario secundario SUNAT con permisos minimos de consulta.
- Confirmacion de que ninguna empresa entregara Clave SOL principal.

## Estado de cierre

Matriz lista para piloto controlado con almacenamiento cifrado/vault. La conexion SUNAT real no debe activarse hasta tener conector read-only aprobado y validacion CEO.
