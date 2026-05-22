from __future__ import annotations

from fastapi import HTTPException, status


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "super_admin": {
        "*",
    },
    "tenant_admin": {
        "dashboard:read",
        "runtime:read",
        "users:read",
        "subscriptions:read",
        "alerts:read",
        "alerts:write",
        "recommendations:read",
        "recommendations:write",
        "documents:read",
        "documents:write",
        "education:read",
        "workflows:read",
        "workflows:write",
        "workflows:advance",
        "workflows:high_risk",
        "governance:read",
        "governance:create",
        "governance:decide",
        "ai:read",
        "ai:request",
        "knowledge:read",
    },
    "operator": {
        "dashboard:read",
        "runtime:read",
        "users:read",
        "subscriptions:read",
        "alerts:read",
        "alerts:write",
        "recommendations:read",
        "recommendations:write",
        "documents:read",
        "documents:write",
        "education:read",
        "workflows:read",
        "workflows:write",
        "workflows:advance",
        "ai:read",
        "ai:request",
        "knowledge:read",
    },
    "auditor": {
        "dashboard:read",
        "runtime:read",
        "users:read",
        "subscriptions:read",
        "alerts:read",
        "recommendations:read",
        "documents:read",
        "education:read",
        "workflows:read",
        "governance:read",
        "ai:read",
        "knowledge:read",
    },
    "readonly": {
        "dashboard:read",
        "runtime:read",
        "users:read",
        "subscriptions:read",
        "alerts:read",
        "recommendations:read",
        "documents:read",
        "education:read",
        "workflows:read",
        "governance:read",
        "ai:read",
        "knowledge:read",
    },
}


def permissions_for_role(role: str) -> list[str]:
    permissions = ROLE_PERMISSIONS.get(role, set())
    if "*" in permissions:
        expanded = set().union(*(value for key, value in ROLE_PERMISSIONS.items() if key != "super_admin"))
        expanded.add("*")
        return sorted(expanded)
    return sorted(permissions)


def has_permission(role: str, permission: str) -> bool:
    permissions = ROLE_PERMISSIONS.get(role, set())
    return "*" in permissions or permission in permissions


def enforce_permission(role: str, permission: str) -> None:
    if not has_permission(role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "permission_denied", "permission": permission},
        )
