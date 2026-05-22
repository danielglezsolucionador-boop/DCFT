from __future__ import annotations


PLANS = [
    {
        "id": "free_student",
        "name": "Free / Student",
        "login_required": False,
        "features": ["accounting_exercises", "finance_exercises", "tax_education", "basic_simulations"],
        "locked_features": ["business_monitoring", "executive_reports", "sunat_document_support"],
    },
    {
        "id": "business_basic",
        "name": "Business Basic",
        "login_required": True,
        "features": ["basic_monitoring", "alerts", "document_analysis", "basic_cross_checks"],
        "limits": {"recommendations_per_month": 50},
    },
    {
        "id": "business_premium",
        "name": "Business Premium",
        "login_required": True,
        "features": ["advanced_recommendations", "deep_simulations", "executive_reports", "advanced_audit", "sunat_document_support"],
        "limits": {"recommendations_per_month": 500},
    },
]


class SubscriptionService:
    def plans(self) -> list[dict]:
        return PLANS

    def current(self, plan: str = "free_student") -> dict:
        return next((item for item in PLANS if item["id"] == plan), PLANS[0])


subscription_service = SubscriptionService()