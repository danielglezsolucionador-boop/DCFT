from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
REGULATORY_ROOT = ROOT / "data" / "regulatory"
TEXT_EXTENSIONS = {".html", ".htm", ".txt", ".md", ".json", ".csv"}
MAX_TEXT_CHARS = 20_000


def _read_text(path: Path) -> str:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:MAX_TEXT_CHARS]
    except OSError:
        return ""


class RegulatoryCorpusService:
    def list_items(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        if not REGULATORY_ROOT.exists():
            return items
        for metadata_path in sorted(REGULATORY_ROOT.glob("*/metadata/*.json")):
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            raw_file = metadata.get("raw_file") or ""
            raw_path = metadata_path.parents[1] / "raw" / raw_file
            raw_text = _read_text(raw_path) if raw_path.exists() else ""
            items.append(
                {
                    "id": metadata.get("dataset_id") or metadata_path.stem,
                    "title": metadata.get("source_title") or metadata.get("source_id") or metadata_path.stem,
                    "source_id": metadata.get("source_id"),
                    "category": metadata.get("category"),
                    "jurisdiction": metadata.get("jurisdiction"),
                    "publisher": metadata.get("publisher"),
                    "source_url": metadata.get("source_url"),
                    "raw_file": raw_file,
                    "sha256": metadata.get("sha256"),
                    "provenance_status": metadata.get("provenance_status"),
                    "metadata_path": str(metadata_path.relative_to(ROOT)).replace("\\", "/"),
                    "text_excerpt": raw_text,
                }
            )
        return items


regulatory_corpus_service = RegulatoryCorpusService()
