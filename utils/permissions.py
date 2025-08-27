# utils/permissions.py
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterable, List

import yaml

logger = logging.getLogger("permissions")

# Projektwurzel (utils/ liegt eine Ebene unterhalb)
BASE_DIR = Path(__file__).resolve().parents[1]
CFG_PATH = Path(os.getenv("CONFIG_PATH") or (BASE_DIR / "config.yml"))

try:
    with open(CFG_PATH, "r", encoding="utf-8") as f:
        _CFG = yaml.safe_load(f) or {}
except FileNotFoundError:
    _CFG = {}

_PERM = _CFG.get("permissions", {}) or {}

# Flags
ALLOW_ADMIN_PERM: bool = bool(_PERM.get("allow_admin_perm", True))
ALLOW_GUILD_OWNER: bool = bool(_PERM.get("allow_guild_owner", True))

def _parse_id_list(text: str) -> List[int]:
    out: List[int] = []
    text = (text or "").replace(";", ",")
    for chunk in text.split(","):
        s = chunk.strip()
        if not s:
            continue
        try:
            out.append(int(s))
        except ValueError:
            # harmless: skip
            pass
    return out

# Rollen-/User-IDs aus config.yml
ROLE_IDS: List[int] = []
USER_IDS: List[int] = []

for x in _PERM.get("role_ids", []) or []:
    try:
        ROLE_IDS.append(int(x))
    except Exception:
        pass

for x in _PERM.get("user_ids", []) or []:
    try:
        USER_IDS.append(int(x))
    except Exception:
        pass

# Merge mit .env (kommagetrennt)
ROLE_IDS = list(dict.fromkeys(ROLE_IDS + _parse_id_list(os.getenv("ADMIN_ROLE_IDS", ""))))
USER_IDS = list(dict.fromkeys(USER_IDS + _parse_id_list(os.getenv("ADMIN_USER_IDS", ""))))

# Optionales Debug-Logging
DEBUG: bool = bool(_PERM.get("debug", False) or os.getenv("PERMISSIONS_DEBUG", "").lower() in ("1", "true", "yes"))

def _has_any_role_id(member, role_ids: Iterable[int]) -> bool:
    try:
        member_role_ids = {r.id for r in getattr(member, "roles", [])}
        return any(rid in member_role_ids for rid in role_ids)
    except Exception:
        return False

def user_is_admin(user) -> bool:
    """
    Policy:
      1) Allow if in USER_IDS
      2) Allow if guild owner (when enabled)
      3) Allow if has Administrator perm (when enabled)
      4) Allow if has any role from ROLE_IDS
      else: deny
    """
    try:
        uid = getattr(user, "id", None)

        # 1) Whitelist
        if USER_IDS and uid in USER_IDS:
            if DEBUG: logger.info("permissions: allow user %s by USER_IDS", uid)
            return True

        # 2) Guild Owner
        if ALLOW_GUILD_OWNER:
            try:
                if getattr(user, "guild", None) and user.id == user.guild.owner_id:
                    if DEBUG: logger.info("permissions: allow user %s by guild owner", uid)
                    return True
            except Exception:
                pass

        # 3) Administrator-Permission
        if ALLOW_ADMIN_PERM:
            try:
                if getattr(getattr(user, "guild_permissions", None), "administrator", False):
                    if DEBUG: logger.info("permissions: allow user %s by admin perm", uid)
                    return True
            except Exception:
                pass

        # 4) Rollencheck
        if ROLE_IDS:
            try:
                if _has_any_role_id(user, ROLE_IDS):
                    if DEBUG: logger.info("permissions: allow user %s by role id match (%s)", uid, ROLE_IDS)
                    return True
            except Exception:
                pass

        if DEBUG:
            try:
                current_roles = [getattr(r, "id", "?") for r in getattr(user, "roles", [])]
                is_admin = getattr(getattr(user, "guild_permissions", None), "administrator", False)
                is_owner = bool(getattr(user, "guild", None) and user.id == user.guild.owner_id)
            except Exception:
                current_roles, is_admin, is_owner = [], False, False
            logger.info("permissions: DENY user %s (roles=%s admin=%s owner=%s)", uid, current_roles, is_admin, is_owner)

        return False

    except Exception as e:
        if DEBUG:
            logger.exception("permissions: exception in user_is_admin: %s", e)
        return False
