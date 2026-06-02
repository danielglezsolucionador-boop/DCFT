# Jurisprudence Dataset Foundation

Controlled intake area for Peruvian jurisprudence sources relevant to DCFT.

No synthetic jurisprudence is allowed here. Raw files must come from official public sources and remain `manual_review_required` until a human validates scope, legal relevance, and update cadence.

## Directory Layout

- `sources/jurisprudence_sources.json`: approved source registry.
- `raw/`: acquired official source files.
- `metadata/`: provenance manifests with hash and source data.
- `processed/`: normalized outputs after later review.

## Boundaries

1. Prefer primary public sources: MEF/Tribunal Fiscal, Poder Judicial/gob.pe, Tribunal Constitucional.
2. Do not infer legal doctrine without source citation and human review.
3. Do not scrape authenticated systems or personal case data.
4. Keep each acquired raw file hash-versioned.
5. Do not use these files for legal advice or autonomous action.
