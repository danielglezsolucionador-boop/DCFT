# DCFT Implementation Matrix

DCFT is implemented as a local-first operational foundation for a premium accounting, financial, and tax assistant. The current system is intentionally conservative: it records, explains, validates, and blocks critical actions behind human governance.

## Operational Boundaries

- No cloud deployment.
- No remote repository.
- No external AI provider.
- No official tax filing.
- No SUNAT, bank, or official document mutation.
- No cross-tenant data sharing.
- Critical actions require human governance and remain blocked by default.

## Implemented Local Systems

- FastAPI backend with `/health`, `/runtime/status`, auth, subscriptions, dashboard, alerts, recommendations, documents, education, workflows, governance, AI request registry, and knowledge registry endpoints.
- PostgreSQL-ready SQLAlchemy and Alembic schema with local SQLite fallback for development.
- JWT auth with local bootstrap credentials.
- Plan model: `free_student`, `business_basic`, `business_premium`.
- JSONL audit trail and local JSON operational stores under `.dcft`.
- React/Vite/Tailwind frontend consuming the backend directly.
- Validation script and pytest coverage for security, governance, provider-disabled behavior, and workflow checkpoints.

## Current Readiness

The system is ready for strong local testing. It is not production-ready until real local/prod secrets, PostgreSQL, non-wildcard CORS, and cloud deployment controls are configured.