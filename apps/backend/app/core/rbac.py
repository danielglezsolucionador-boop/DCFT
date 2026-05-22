from __future__ import annotations

from fastapi import HTTPException, status


ROLE_HIERARCHY: dict[str, int] = {
    "readonly": 10,
    "auditor": 20,
    "operator": 30,
    "tenant_admin": 40,
    "super_admin": 50,
}


ROLE_PERMISSIONS: dict[str, set[str]] = {
    "super_admin": {
        "*",
    },
    "tenant_admin": {
        "dashboard:read",
        "runtime:read",
        "users:read",
        "subscriptions:read",
        "subscriptions:manage",
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
        "audit:read",
        "analytics:read",
        "analytics:write",
        "feedback:write",
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
        "analytics:write",
        "feedback:write",
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
        "audit:read",
        "analytics:read",
        "feedback:write",
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
        "audit:read",
        "analytics:read",
        "feedback:write",
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


def role_rank(role: str) -> int:
    return ROLE_HIERARCHY.get(role, 0)


def has_role_at_least(role: str, minimum_role: str) -> bool:
    return role_rank(role) >= role_rank(minimum_role)


def enforce_permission(role: str, permission: str) -> None:
    if not has_permission(role, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "permission_denied", "permission": permission},
        )


def enforce_role_at_least(role: str, minimum_role: str) -> None:
    if not has_role_at_least(role, minimum_role):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "role_denied", "minimum_role": minimum_role},
        )
