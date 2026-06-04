# DCFT User Testing Checklist

## Antes de probar

- Usar la URL oficial del frontend DCFT.
- Crear un usuario nuevo.
- Elegir el tipo de cuenta correcto: Estudiante o Empresa.
- No ingresar Clave SOL principal.
- No compartir secretos por chat, formularios o capturas.

## Pruebas de cuenta

- Registro de usuario nuevo funciona.
- Login funciona.
- Logout funciona.
- Login posterior conserva la cuenta.
- El usuario ve su plan base.
- El usuario ve si tiene Premium de prueba activo.

## Pruebas por plan

- Estudiante puede crear cuenta sin RUC.
- MYPE sin RUC debe ser bloqueado.
- MYPE con RUC crea empresa.
- MYPE con RUC crea workspace.
- Premium de prueba muestra dias restantes.
- Al desactivar trial, los datos no se borran.

## Onboarding

- Video 1 visible: Crear usuario secundario SUNAT.
- Video 2 visible: Conectar empresa a DCFT.
- Video 3 visible: Interpretar diagnostico empresarial.
- Cada video puede marcarse como visto.
- El estado visto persiste tras recargar.
- El checklist muestra cuenta, empresa, RUC, videos, SUNAT auxiliar, diagnostico y trial.

## SUNAT auxiliar

- El flujo explica que DCFT solo consulta.
- El flujo indica que DCFT no declara, no paga, no firma y no modifica informacion.
- El campo recomendado es usuario secundario/auxiliar.
- No se solicita Clave SOL principal.
- No se solicita password en esta foundation.
- El boton de validar conexion queda pendiente/deshabilitado mientras no exista conector real.

## Admin CEO

- El panel admin no aparece para usuarios normales.
- Admin CEO puede listar usuarios.
- Admin CEO puede activar Premium trial 7 dias.
- Admin CEO puede desactivar trial.
- Admin CEO puede cambiar plan manualmente.
- Los cambios persisten despues de logout/login.

## Evidencia a capturar

- Registro exitoso.
- Login exitoso.
- Dashboard con empresa/workspace si aplica.
- Badge Premium de prueba con dias restantes.
- Checklist de onboarding.
- Videos marcados como vistos.
- SUNAT auxiliar preparado sin clave.
- Panel Admin CEO protegido.
