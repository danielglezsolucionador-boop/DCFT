from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

from app.db import repositories
from app.services.knowledge_service import knowledge_service
from app.services.regulatory_corpus_service import regulatory_corpus_service
from app.services.regulatory_service import regulatory_service


TOKEN_RE = re.compile(r"[a-zA-Z0-9áéíóúÁÉÍÓÚñÑ]{3,}")
DEFAULT_DIMENSIONS = 64


def _tokens(value: str) -> list[str]:
    return [match.group(0).lower() for match in TOKEN_RE.finditer(value)]


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _stable_index(token: str, dimensions: int) -> int:
    digest = hashlib.sha256(token.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % dimensions


def _stable_sign(token: str) -> float:
    digest = hashlib.sha256(f"sign:{token}".encode("utf-8")).digest()
    return 1.0 if digest[0] % 2 == 0 else -1.0


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 8) for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    return round(sum(a * b for a, b in zip(left, right)), 8)


class EmbeddingService:
    def embed_text(self, text: str, dimensions: int = DEFAULT_DIMENSIONS) -> list[float]:
        vector = [0.0] * dimensions
        for token in _tokens(text):
            vector[_stable_index(token, dimensions)] += _stable_sign(token)
        return _normalize(vector)

    async def search(self, tenant_id: str, query: str, limit: int = 10, dimensions: int = DEFAULT_DIMENSIONS) -> dict:
        query_vector = self.embed_text(query, dimensions)
        candidates: list[dict] = []
        for item in knowledge_service.list_items():
            candidates.append({"source": "knowledge_registry", "source_id": item["id"], "title": item.get("title", item["id"]), "payload": item})
        for item in regulatory_service.list_items():
            candidates.append({"source": "regulatory_registry", "source_id": item["id"], "title": item.get("title", item["id"]), "payload": item})
        for item in regulatory_corpus_service.list_items():
            candidates.append({"source": "regulatory_dataset", "source_id": item["id"], "title": item.get("title", item["id"]), "payload": item})
        for item in await repositories.list_memory_records(tenant_id, limit=500):
            candidates.append({"source": "tenant_memory", "source_id": item["id"], "title": item.get("memory_type", "memory"), "payload": item})

        ranked = []
        for candidate in candidates:
            vector = self.embed_text(_text(candidate["payload"]), dimensions)
            similarity = _cosine(query_vector, vector)
            if similarity <= 0:
                continue
            ranked.append(
                {
                    "source": candidate["source"],
                    "source_id": candidate["source_id"],
                    "title": candidate["title"],
                    "similarity": similarity,
                    "embedding_model": "local_hash_embedding_v1",
                    "embedding_dimensions": dimensions,
                    "payload": candidate["payload"],
                }
            )
        ranked.sort(key=lambda item: (-item["similarity"], item["source"], item["source_id"]))
        return {
            "query": query,
            "tenant_id": tenant_id,
            "embedding_model": "local_hash_embedding_v1",
            "embedding_dimensions": dimensions,
            "candidate_count": len(candidates),
            "result_count": min(len(ranked), limit),
            "query_embedding": query_vector,
            "results": ranked[:limit],
        }


embedding_service = EmbeddingService()
