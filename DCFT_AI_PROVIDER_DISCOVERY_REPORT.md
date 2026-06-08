# DCFT AI Provider Discovery Report

Fecha local: 2026-06-07

## Estado

Listo para revision CEO.

## Regla CEO

- Estado maximo permitido: `Listo para revision CEO.`
- La decision final solo puede venir del CEO de forma explicita.

## DCFT antes del cambio

- DCFT tenia `DCFT_AI_PROVIDER_ENABLED` como bandera de proveedor.
- No tenia variables propias de key/modelo por proveedor IA en los `.env*.example`.
- El pipeline productivo reportaba `ai_pipeline=blocked_provider_disabled`.

## Ecosistema revisado

FORJA:

- Usa OpenRouter desde backend.
- Variables detectadas: `OPENROUTER_API_KEY`, `FORJA_OPENROUTER_API_KEY`, `FORJA_OPENROUTER_MODEL`, `OPENROUTER_MODEL`.
- Endpoint detectado: `https://openrouter.ai/api/v1/chat/completions`.
- Modelos/fallbacks detectados: `openai/gpt-4o-mini`, `openrouter/free`.

CEREBRO:

- `C:\Users\admin\Desktop\cerebro-app\server.js` usa OpenRouter.
- Variables detectadas: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `ANTHROPIC_API_KEY`.
- Endpoint detectado: `https://openrouter.ai/api/v1/chat/completions`.
- Tambien contiene llamada Anthropic con header `x-api-key`.

CEREBRO backend:

- Contiene referencias futuras a rutas Anthropic/OpenAI/Gemini y abstraccion de proveedores.

## Decision tecnica aplicada a DCFT

Se agrego soporte controlado para:

- `openrouter`
- `openai`
- `anthropic`
- `gemini`

OpenRouter queda como proveedor por defecto porque ya existe patron operativo en FORJA/CEREBRO y permite compatibilidad tipo OpenAI.

## Variables DCFT agregadas

- `DCFT_AI_PROVIDER_ENABLED`
- `DCFT_AI_PROVIDER`
- `DCFT_AI_MODEL`
- `DCFT_AI_REQUEST_TIMEOUT_SECONDS`
- `DCFT_OPENROUTER_API_KEY`
- `DCFT_OPENROUTER_MODEL`
- `DCFT_OPENROUTER_BASE_URL`
- `DCFT_OPENROUTER_REFERER`
- `DCFT_OPENROUTER_TITLE`
- `DCFT_OPENAI_API_KEY`
- `DCFT_OPENAI_MODEL`
- `DCFT_ANTHROPIC_API_KEY`
- `DCFT_ANTHROPIC_MODEL`
- `DCFT_GEMINI_API_KEY`
- `DCFT_GEMINI_MODEL`

## Politica de seguridad

- No se imprimieron valores de secretos.
- Los reportes solo registran nombres de variables.
- Los `.env*.example` contienen placeholders.
- Si `DCFT_AI_PROVIDER_ENABLED=false` o falta key, el Doctor devuelve bloqueo honesto `ai_provider_missing=true`.

## Riesgos

- Produccion requiere configurar secret real en Vercel o secret manager.
- La activacion debe hacerse primero en entorno controlado.
- El modelo final debe confirmarse por costo, latencia y politica de datos antes de exposicion amplia.
