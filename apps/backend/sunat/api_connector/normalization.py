from __future__ import annotations


def normalize_cpe_response(result: dict) -> list[dict]:
    raw = result.get("raw") or {}
    data = raw.get("data") if isinstance(raw, dict) else {}
    if not isinstance(data, dict):
        data = {}
    return [
        {
            "fact_type": "cpe_validity",
            "fact_key": "estado_comprobante",
            "fact_value": {
                "estado_cp": data.get("estadoCp"),
                "estado_ruc": data.get("estadoRuc"),
                "condicion_domicilio": data.get("condDomiRuc"),
                "observaciones": data.get("Observaciones") or data.get("observaciones") or [],
                "success": raw.get("success"),
                "message": raw.get("message"),
            },
            "confidence": 90,
        }
    ]


def normalize_sire_sales_response(result: dict) -> list[dict]:
    return [
        {
            "fact_type": "sire_sales",
            "fact_key": str(result.get("period") or "period"),
            "fact_value": {
                "period": result.get("period"),
                "content_type": result.get("content_type"),
                "raw_text_available": bool(result.get("raw_text")),
            },
            "confidence": 75,
        }
    ]


def normalize_sire_purchases_response(result: dict) -> list[dict]:
    raw = result.get("raw")
    return [
        {
            "fact_type": "sire_purchases",
            "fact_key": str(result.get("period") or "period"),
            "fact_value": {
                "period": result.get("period"),
                "raw_available": raw is not None,
                "raw_keys": sorted(raw.keys()) if isinstance(raw, dict) else [],
            },
            "confidence": 75,
        }
    ]
