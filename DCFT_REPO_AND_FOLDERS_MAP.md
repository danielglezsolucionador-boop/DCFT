# DCFT Repo And Folders Map

Fecha local: 2026-06-06

## Objetivo

Este documento fija el mapa oficial de carpetas DCFT para evitar confusion futura. No borra, mueve ni limpia carpetas. Cualquier limpieza posterior debe hacerse solo con backup previo y aprobacion humana.

## Repo Oficial DCFT

| Campo | Valor |
| --- | --- |
| Repo oficial | `C:\Users\admin\dcft-knowledge-core` |
| Clasificacion | OFICIAL |
| Remote origin | `https://github.com/danielglezsolucionador-boop/DCFT.git` |
| Branch | `main` |
| Ultimo commit local/pushed | `e987f6b fix: polish dcft student access flow` |
| Worktree | principal, no bare |
| Frontend real | `apps/frontend` |
| Backend real | `apps/backend` y `api/index.py` |
| Frontend produccion asociado | `https://dcft-frontend.vercel.app` |
| Backend produccion asociado | `https://dcft.vercel.app` |
| Vercel backend local project | `.vercel/project.json` -> `projectName=dcft` |
| Vercel frontend local project | `apps/frontend/.vercel/project.json` -> `projectName=dcft-frontend` |

Siempre usar esta carpeta para cambios, validaciones, commits y push de DCFT.

## Estado Git Observado

- Branch: `main`.
- Remote: `origin https://github.com/danielglezsolucionador-boop/DCFT.git`.
- Ultimo commit: `e987f6b fix: polish dcft student access flow`.
- Hay archivos locales modificados/untracked previos en reportes SUNAT/auditoria. No fueron borrados ni movidos.
- Este documento se crea como control local; no implica push ni deploy.

## Carpetas Encontradas

| Ruta | .git | Remote | Branch | Ultimo commit | Frontend | Backend | Reportes | Modificacion aprox. | Clasificacion | Riesgo de confusion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `C:\Users\admin\dcft-knowledge-core` | SI | `https://github.com/danielglezsolucionador-boop/DCFT.git` | `main` | `e987f6b fix: polish dcft student access flow` | SI | SI | SI, 26+ | 2026-06-06 22:00 | OFICIAL | Alto si no se identifica como unica fuente productiva |
| `C:\Users\admin\cerebro\cerebro\forja-knowledge-core\dcft-knowledge-core` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-05-21 | COPIA VIEJA / HISTORICA | Medio; nombre parece repo pero no tiene Git ni app completa |
| `C:\Users\admin\dcft-backups` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-05-23 | BACKUP CONTENEDOR | Medio; contiene backups con nombres DCFT |
| `C:\Users\admin\dcft-backups\DCFT_PREMIUM_PRE_UI_FREEZE_20260522_090709` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-05-22 | BACKUP | Medio; freeze historico |
| `C:\Users\admin\dcft-backups\dcft-backup-20260522-033918` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-05-22 | BACKUP | Bajo; carpeta pequena |
| `C:\Users\admin\dcft-backups\dcft-extreme-audit-pre-20260522-035202` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-05-22 | BACKUP | Bajo |
| `C:\Users\admin\dcft-backups\dcft-hardening-pre-20260522-042239` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-05-22 | BACKUP | Bajo |
| `C:\Users\admin\Documents\Codex\2026-05-22\dcft-premium-apple-level-ui-redesign` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-05-22 | ARCHIVO HISTORICO | Bajo; sesion Codex antigua |
| `C:\Users\admin\Documents\Codex\2026-05-24\dcft-fase-1-apple-grade-premium` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-05-24 | ARCHIVO HISTORICO | Bajo; sesion Codex antigua |
| `C:\Users\admin\Documents\Codex\2026-05-31\auditoria-final-forja-render-he-validado\work\dcft-frontend-vercel-deploy` | NO | N/A | N/A | N/A | SI | NO | NO | 2026-06-04 | COPIA / WORK AUXILIAR | Alto; parece frontend deployable pero no es repo oficial |
| `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-06-05 | CARPETA DE SESION CODEX | Medio; contiene outputs/work/capturas |
| `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\dcft-backend-ephemeral` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-06-05 | WORK AUXILIAR / EPHEMERAL | Medio; nombre sugiere backend pero no es repo |
| `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\chrome-dcft-prod-ui` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-06-05 | CAPTURA / PERFIL BROWSER | Bajo |
| `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\chrome-dcft-prod-sunat-ui` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-06-05 | CAPTURA / PERFIL BROWSER | Bajo |
| `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\edge-dcft-local-desktop` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-06-06 | CAPTURA / PERFIL BROWSER | Bajo |
| `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\edge-dcft-local-mobile` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-06-05 | CAPTURA / PERFIL BROWSER | Bajo |
| `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\edge-dcft-prod-shot-desktop` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-06-05 | CAPTURA / PERFIL BROWSER | Bajo |
| `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\edge-dcft-prod-shot-mobile` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-06-05 | CAPTURA / PERFIL BROWSER | Bajo |
| `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\edge-dcft-shot-desktop2` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-06-05 | CAPTURA / PERFIL BROWSER | Bajo |
| `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\edge-dcft-shot-mobile2` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-06-05 | CAPTURA / PERFIL BROWSER | Bajo |
| `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613\forja-knowledge-core\dcft-knowledge-core` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-05-28 | BACKUP HISTORICO | Bajo; esta dentro de backup CEREBRO |
| `D:\ECOSYSTEM\BACKUPS\stage-phase2-20260526-175348\CEREBRO\forja-knowledge-core\dcft-knowledge-core` | NO | N/A | N/A | N/A | NO | NO | NO | 2026-05-21 | BACKUP HISTORICO | Bajo; esta dentro de backup CEREBRO |

## Clasificacion Operativa

### OFICIAL

- `C:\Users\admin\dcft-knowledge-core`

### BACKUP

- `C:\Users\admin\dcft-backups`
- `C:\Users\admin\dcft-backups\DCFT_PREMIUM_PRE_UI_FREEZE_20260522_090709`
- `C:\Users\admin\dcft-backups\dcft-backup-20260522-033918`
- `C:\Users\admin\dcft-backups\dcft-extreme-audit-pre-20260522-035202`
- `C:\Users\admin\dcft-backups\dcft-hardening-pre-20260522-042239`
- `D:\ECOSYSTEM\BACKUPS\CEREBRO_FINAL_CLOSURE_20260528-222613\forja-knowledge-core\dcft-knowledge-core`
- `D:\ECOSYSTEM\BACKUPS\stage-phase2-20260526-175348\CEREBRO\forja-knowledge-core\dcft-knowledge-core`

### COPIA VIEJA / ARCHIVO HISTORICO

- `C:\Users\admin\cerebro\cerebro\forja-knowledge-core\dcft-knowledge-core`
- `C:\Users\admin\Documents\Codex\2026-05-22\dcft-premium-apple-level-ui-redesign`
- `C:\Users\admin\Documents\Codex\2026-05-24\dcft-fase-1-apple-grade-premium`

### WORK AUXILIAR / CAPTURAS

- `C:\Users\admin\Documents\Codex\2026-05-31\auditoria-final-forja-render-he-validado\work\dcft-frontend-vercel-deploy`
- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber`
- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\dcft-backend-ephemeral`
- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\chrome-dcft-prod-ui`
- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\chrome-dcft-prod-sunat-ui`
- `C:\Users\admin\Documents\Codex\2026-06-05\dcft-verificar-si-vercel-ya-liber\work\edge-dcft-*`

## Que Carpeta Usar Siempre

Usar siempre:

`C:\Users\admin\dcft-knowledge-core`

Para frontend:

`C:\Users\admin\dcft-knowledge-core\apps\frontend`

Para backend:

`C:\Users\admin\dcft-knowledge-core\apps\backend`

Para Vercel backend:

`C:\Users\admin\dcft-knowledge-core`

Para Vercel frontend:

`C:\Users\admin\dcft-knowledge-core\apps\frontend`

## Carpetas No Tocar

No tocar sin autorizacion:

- Todas las carpetas dentro de `D:\ECOSYSTEM\BACKUPS`.
- Todas las carpetas dentro de `C:\Users\admin\dcft-backups`.
- Carpetas de sesion/captura en `C:\Users\admin\Documents\Codex\...`.
- Copia vieja dentro de `C:\Users\admin\cerebro\...` porque puede servir como evidencia historica de CEREBRO/FORJA.

## Carpetas Que Podrian Archivarse Despues

Solo despues de crear un backup consolidado y con aprobacion CEO:

- Sesiones Codex antiguas con `dcft-*`.
- Perfiles/capturas `chrome-dcft-*` y `edge-dcft-*`.
- Work auxiliar `dcft-frontend-vercel-deploy` si se confirma que no contiene evidencia necesaria.

## Recomendacion De Limpieza Futura

1. Crear backup completo de todas las carpetas candidatas.
2. Comparar contra el repo oficial.
3. Extraer solo reportes/evidencias utiles.
4. Archivar carpetas de captura/work en un zip fechado.
5. No borrar nada hasta validar que el backup abre y contiene los archivos esperados.

## Advertencia

No borrar carpetas DCFT sin backup previo verificado. No usar carpetas sin `.git` para cambios productivos. No hacer deploy desde carpetas de work, capturas, backups o sesiones Codex.
