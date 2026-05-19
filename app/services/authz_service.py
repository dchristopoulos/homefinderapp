BASE_PERMISSIONS = {
    "read",
    "write",
    "search",
    "favorite",
    "inquiry",
    "reserve",
    "schedule_viewing",
    "manage_own_listings",
}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "regular_user": {
        *BASE_PERMISSIONS,
    },
    "property_owner": {
        *BASE_PERMISSIONS,
        "view_owner_inquiries",
    },
    "service_supervisor": {
        "read",
        "write",
        "search",
        "inquiry",
        "view_reports",
    },
    "admin": {
        *BASE_PERMISSIONS,
        "view_owner_inquiries",
        "manage_listings",
        "manage_users",
        "view_reports",
        "manage_permissions",
        "delete_users",
    },
}

ALL_PERMISSIONS = sorted({permission for perms in ROLE_PERMISSIONS.values() for permission in perms})


def _parse_permission_list(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {part.strip() for part in raw.split(",") if part.strip()}


def get_effective_permissions(role: str, permission_grants: str | None = None, permission_revokes: str | None = None) -> set[str]:
    base = set(ROLE_PERMISSIONS.get(role, set()))
    grants = _parse_permission_list(permission_grants)
    revokes = _parse_permission_list(permission_revokes)
    base.update(grants)
    base.difference_update(revokes)
    return base


def has_permission(
    role: str,
    permission: str,
    permission_grants: str | None = None,
    permission_revokes: str | None = None,
) -> bool:
    return permission in get_effective_permissions(role, permission_grants, permission_revokes)
