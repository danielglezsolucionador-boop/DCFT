from __future__ import annotations


OFFICIAL_SUNAT_AUTOMATION_SERVICES = [
    {
        "service": "cpe",
        "label": "Consulta integrada de validez de comprobantes",
        "official_api_available": True,
        "requires_api_credentials": True,
        "requires_sol_credentials": False,
        "scope": "https://api.sunat.gob.pe/v1/contribuyente/contribuyentes",
        "read_only": True,
        "status": "available_for_test",
    },
    {
        "service": "sire_sales",
        "label": "SIRE Ventas RVIE",
        "official_api_available": True,
        "requires_api_credentials": True,
        "requires_sol_credentials": True,
        "scope": "https://api-sire.sunat.gob.pe",
        "read_only": True,
        "status": "available_for_test",
    },
    {
        "service": "sire_purchases",
        "label": "SIRE Compras RCE",
        "official_api_available": True,
        "requires_api_credentials": True,
        "requires_sol_credentials": True,
        "scope": "https://api-sire.sunat.gob.pe",
        "read_only": True,
        "status": "available_for_test",
    },
    {
        "service": "declarations_payments",
        "label": "Declaraciones y pagos",
        "official_api_available": False,
        "requires_sol_credentials": True,
        "read_only": False,
        "status": "ONLY_SOL_WEB",
    },
    {
        "service": "debts_values",
        "label": "Deudas y valores pendientes",
        "official_api_available": False,
        "requires_sol_credentials": True,
        "read_only": True,
        "status": "ONLY_SOL_WEB",
    },
    {
        "service": "files_writings",
        "label": "Expedientes y escritos",
        "official_api_available": False,
        "requires_sol_credentials": True,
        "read_only": False,
        "status": "ONLY_SOL_WEB",
    },
]


class SunatApiDiscovery:
    def catalog(self, *, api_configured: bool, sol_configured: bool, service_status: dict | None = None) -> dict:
        statuses = service_status or {}
        services = []
        for service in OFFICIAL_SUNAT_AUTOMATION_SERVICES:
            current = dict(service)
            saved = statuses.get(service["service"]) or {}
            if saved:
                current.update(saved)
            if service.get("official_api_available") is False:
                current["status"] = service["status"]
            elif service.get("requires_api_credentials") and not api_configured:
                current["status"] = "API_CREDENTIALS_MISSING"
            elif service.get("requires_sol_credentials") and not sol_configured:
                current["status"] = "SOL_CREDENTIALS_MISSING"
            services.append(current)
        return {
            "services": services,
            "api_configured": api_configured,
            "sol_configured": sol_configured,
            "read_only": True,
            "sensitive_actions_enabled": False,
        }
