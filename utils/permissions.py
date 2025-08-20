import os
from typing import Set

ADMIN_ROLE_IDS: Set[int] = {
    int(x) for x in (os.getenv("ADMIN_ROLE_IDS") or "").split(",") if x.strip().isdigit()
}

def user_is_admin(member) -> bool:
    """True, wenn Nutzer Admin ist (Server-Admin oder Rolle in ADMIN_ROLE_IDS)."""
    if member is None:
        return False
    try:
        if getattr(member, "guild_permissions", None) and member.guild_permissions.administrator:
            return True
    except Exception:
        pass
    user_roles = {getattr(r, "id", None) for r in (getattr(member, "roles", []) or [])}
    user_roles.discard(None)
    return not user_roles.isdisjoint(ADMIN_ROLE_IDS)
