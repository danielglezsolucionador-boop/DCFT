from __future__ import annotations


SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}


class SunatApiDiagnostics:
    def findings_from_results(self, results: list[dict]) -> list[dict]:
        findings: list[dict] = []
        for result in results:
            service = str(result.get("service") or "sunat_api")
            status = str(result.get("status") or "")
            if status.endswith("_OK") or status == "TOKEN_OK":
                findings.append(
                    {
                        "severity": "info",
                        "category": service,
                        "title": f"{service} disponible por API oficial",
                        "message": "SUNAT respondió por una ruta API oficial autorizada. DCFT puede usar esta señal para diagnóstico.",
                        "status": "open",
                        "metadata": {"service": service, "api_status": status},
                    }
                )
            else:
                findings.append(
                    {
                        "severity": "medium",
                        "category": service,
                        "title": f"{service} pendiente de autorización API",
                        "message": "No se confirmó acceso automático para este servicio. Revisar credenciales API, permisos o alcance oficial.",
                        "status": "open",
                        "metadata": {"service": service, "api_status": status},
                    }
                )
        return sorted(findings, key=lambda item: SEVERITY_ORDER.get(str(item.get("severity")), 9))
