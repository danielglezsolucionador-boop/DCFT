# DCFT Piloto Asistido - Matriz

Fecha: 2026-06-06

Actualizacion Paquete 3: 2026-06-08. Matriz vigente para piloto asistido local; no poner secretos ni claves.

No poner datos reales todavia. Usar placeholders hasta que CEO/CTO apruebe cada tester.

| Tester | Tipo | RUC | Correo | Plan | Usuario SUNAT auxiliar creado | Consentimiento aceptado | Vault guardado | Status verificado | Diagnostico | Semaforo | Feedback | Bloqueos | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<tester_estudiante_1>` | Estudiante | No aplica | `<correo_estudiante>` | Estudiante | No aplica | No aplica | No aplica | No aplica | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| `<tester_mype_1>` | Empresa MYPE | `<ruc_autorizado_mype>` | `<correo_mype>` | MYPE | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |
| `<tester_premium_1>` | Empresa Premium | `<ruc_autorizado_premium>` | `<correo_premium>` | Premium o trial Premium | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente | Pendiente |

## Participantes minimos

- 1 estudiante real/controlado.
- 1 empresa MYPE autorizada.
- 1 empresa Premium o trial Premium autorizada.

## Evidencia minima por empresa

- RUC autorizado registrado.
- Consentimiento aceptado.
- Usuario SUNAT auxiliar creado con permisos de consulta.
- Vault guardado sin exponer clave.
- Status verificado.
- Desconexion ejecutada si el tester lo solicita.
- Diagnostico/semaforo revisado sin inventar datos reales.

## Criterios de decision

- `Continuar`: el flujo fue entendible, seguro y sin bloqueo.
- `Corregir`: hay friccion o bug menor antes de ampliar el piloto.
- `Pausar`: hay duda de seguridad, consentimiento o permisos.
- `Descartar`: el flujo no es apto para piloto real.

## Campos que no deben llenarse

- Password SUNAT.
- Clave SOL principal.
- Tokens.
- Secretos de entorno.
- Capturas que expongan claves.
