from __future__ import annotations


REGULATORY_ITEMS = [
    {
        "id": "pe-tax-disclaimer",
        "jurisdiction": "PE",
        "title": "Peru tax action boundary",
        "status": "active",
        "rule": "DCFT does not file, modify, or submit SUNAT documents automatically.",
    },
    {
        "id": "latam-expansion-boundary",
        "jurisdiction": "LATAM",
        "title": "Jurisdiction isolation",
        "status": "active",
        "rule": "Regulatory content must remain jurisdiction-scoped and reviewed before production use.",
    },
]


class RegulatoryService:
    def list_items(self) -> list[dict]:
        return REGULATORY_ITEMS


regulatory_service = RegulatoryService()