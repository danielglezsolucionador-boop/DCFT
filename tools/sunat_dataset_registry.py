from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SUNAT_DIR = ROOT / "data" / "regulatory" / "sunat"
SOURCES_FILE = SUNAT_DIR / "sources" / "sunat_sources.json"
RAW_DIR = SUNAT_DIR / "raw"
METADATA_DIR = SUNAT_DIR / "metadata"


REQUIRED_SOURCE_FIELDS = {
    "source_id",
    "title",
    "category",
    "source_url",
    "publisher",
    "jurisdiction",
    "acquisition_mode",
    "refresh_cadence",
    "approved_for_pipeline",
}


def load_sources() -> dict[str, Any]:
    with SOURCES_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def source_index(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {source["source_id"]: source for source in registry.get("sources", [])}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def validate_manifest() -> dict[str, Any]:
    registry = load_sources()
    source_ids: set[str] = set()
    errors: list[str] = []
    for index, source in enumerate(registry.get("sources", []), start=1):
        missing = sorted(REQUIRED_SOURCE_FIELDS - set(source))
        if missing:
            errors.append(f"source[{index}] missing fields: {', '.join(missing)}")
        source_id = source.get("source_id")
        if source_id in source_ids:
            errors.append(f"duplicate source_id: {source_id}")
        if source_id:
            source_ids.add(source_id)
        if source.get("publisher") != "SUNAT":
            errors.append(f"{source_id}: publisher must be SUNAT")
        if source.get("jurisdiction") != "PE":
            errors.append(f"{source_id}: jurisdiction must be PE")
        if source.get("acquisition_mode") != "manual_download":
            errors.append(f"{source_id}: acquisition_mode must be manual_download")
        if source.get("approved_for_pipeline") is not True:
            errors.append(f"{source_id}: source is not approved_for_pipeline")
        url = str(source.get("source_url", ""))
        if not (url.startswith("https://www.sunat.gob.pe/") or url.startswith("https://orientacion.sunat.gob.pe/")):
            errors.append(f"{source_id}: source_url is not an approved SUNAT domain")
    return {
        "registry_id": registry.get("registry_id"),
        "sources": len(registry.get("sources", [])),
        "errors": errors,
        "valid": not errors,
    }


def register_file(
    *,
    source_id: str,
    file_path: Path,
    version: str,
    effective_from: str | None,
    effective_to: str | None,
    notes: str,
) -> dict[str, Any]:
    registry = load_sources()
    sources = source_index(registry)
    if source_id not in sources:
        raise SystemExit(f"Unknown source_id: {source_id}")
    resolved = file_path.resolve()
    if not resolved.exists() or not resolved.is_file():
        raise SystemExit(f"Input file not found: {resolved}")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        relative = resolved.relative_to(RAW_DIR.resolve())
    except ValueError:
        raise SystemExit(f"Input file must be inside {RAW_DIR}")

    source = sources[source_id]
    metadata = {
        "dataset_id": f"{source_id}:{version}",
        "source_id": source_id,
        "source_title": source["title"],
        "source_url": source["source_url"],
        "publisher": source["publisher"],
        "jurisdiction": source["jurisdiction"],
        "category": source["category"],
        "acquisition_mode": "manual_download",
        "acquired_at": utc_now(),
        "version": version,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "raw_file": str(relative).replace("\\", "/"),
        "sha256": sha256_file(resolved),
        "size_bytes": resolved.stat().st_size,
        "provenance_status": "manual_review_required",
        "legal_basis": source.get("legal_basis"),
        "usage_notes": source.get("notes"),
        "operator_notes": notes,
    }
    metadata_path = METADATA_DIR / f"{source_id}__{version}.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"metadata_path": str(metadata_path), "metadata": metadata}


def audit_metadata() -> dict[str, Any]:
    registry = load_sources()
    sources = source_index(registry)
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in sorted(METADATA_DIR.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        source_id = record.get("source_id")
        raw_file = record.get("raw_file")
        raw_path = RAW_DIR / raw_file if raw_file else None
        expected_hash = record.get("sha256")
        actual_hash = sha256_file(raw_path) if raw_path and raw_path.exists() else None
        if source_id not in sources:
            errors.append(f"{path.name}: unknown source_id {source_id}")
        if not raw_path or not raw_path.exists():
            errors.append(f"{path.name}: raw file missing")
        if actual_hash and expected_hash != actual_hash:
            errors.append(f"{path.name}: sha256 mismatch")
        records.append(
            {
                "metadata": path.name,
                "source_id": source_id,
                "raw_file": raw_file,
                "hash_ok": bool(actual_hash and actual_hash == expected_hash),
                "provenance_status": record.get("provenance_status"),
            }
        )
    return {
        "metadata_records": len(records),
        "records": records,
        "errors": errors,
        "valid": not errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Controlled SUNAT dataset provenance registry.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate-manifest", help="Validate approved SUNAT source manifest.")
    subparsers.add_parser("audit-metadata", help="Audit registered dataset metadata and raw file hashes.")

    register = subparsers.add_parser("register-file", help="Register a manually downloaded SUNAT file.")
    register.add_argument("--source-id", required=True)
    register.add_argument("--file", required=True, type=Path)
    register.add_argument("--version", required=True)
    register.add_argument("--effective-from")
    register.add_argument("--effective-to")
    register.add_argument("--notes", default="")

    args = parser.parse_args()
    if args.command == "validate-manifest":
        result = validate_manifest()
    elif args.command == "audit-metadata":
        result = audit_metadata()
    else:
        result = register_file(
            source_id=args.source_id,
            file_path=args.file,
            version=args.version,
            effective_from=args.effective_from,
            effective_to=args.effective_to,
            notes=args.notes,
        )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    if result.get("valid") is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
