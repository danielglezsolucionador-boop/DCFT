from __future__ import annotations

import json
import re
from typing import Any

from app.db import repositories
from app.services.knowledge_service import knowledge_service
from app.services.regulatory_corpus_service import regulatory_corpus_service
from app.services.regulatory_service import regulatory_service


TOKEN_RE = re.compile(r"[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]{3,}")


def _tokens(value: str) -> set[str]:
    return {match.group(0).lower() for match in TOKEN_RE.finditer(value)}


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _score(query_tokens: set[str], document_text: str) -> float:
    document_tokens = _tokens(document_text)
    if not query_tokens or not document_tokens:
        return 0.0
    exact = len(query_tokens & document_tokens)
    partial = sum(1 for token in query_tokens if token in document_text.lower()) - exact
    return float((exact * 2) + max(partial, 0))


class RetrievalService:
    async def search(self, tenant_id: str, query: str, limit: int = 10) -> dict:
        query_tokens = _tokens(query)
        candidates: list[dict] = []

        for item in knowledge_service.list_items():
            candidates.append(
                {
                    "source": "knowledge_registry",
                    "source_id": item["id"],
                    "title": item.get("title", item["id"]),
                    "payload": item,
                }
            )

        for item in regulatory_service.list_items():
            candidates.append(
                {
                    "source": "regulatory_registry",
                    "source_id": item["id"],
                    "title": item.get("title", item["id"]),
                    "payload": item,
                }
            )

        for item in regulatory_corpus_service.list_items():
            candidates.append(
                {
                    "source": "regulatory_dataset",
                    "source_id": item["id"],
                    "title": item.get("title", item["id"]),
                    "payload": item,
                }
            )

        for item in await repositories.list_memory_records(tenant_id, limit=500):
            candidates.append(
                {
                    "source": "tenant_memory",
                    "source_id": item["id"],
                    "title": item.get("memory_type", "memory"),
                    "payload": item,
                }
            )

        ranked = []
        for candidate in candidates:
            searchable_text = _text(candidate["payload"])
            score = _score(query_tokens, searchable_text)
            if score <= 0:
                continue
            ranked.append(
                {
                    "source": candidate["source"],
                    "source_id": candidate["source_id"],
                    "title": candidate["title"],
                    "score": score,
                    "payload": candidate["payload"],
                    "matched_terms": sorted(query_tokens & _tokens(searchable_text)),
                }
            )
        ranked.sort(key=lambda item: (-item["score"], item["source"], item["source_id"]))
        return {
            "query": query,
            "tenant_id": tenant_id,
            "strategy": "lexical_token_overlap",
            "candidate_count": len(candidates),
            "result_count": min(len(ranked), limit),
            "results": ranked[:limit],
        }


retrieval_service = RetrievalService()
