from __future__ import annotations
import logging
import os
import socket
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
import requests
import yaml
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# -----------------------------------------------------------------------------
# Pfade & .env
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")  # .env im Skriptordner laden

# -----------------------------------------------------------------------------
# Konfiguration
# -----------------------------------------------------------------------------
CONFIG_PATH = Path(os.getenv("CONFIG_PATH") or (BASE_DIR / "config.yml"))
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        CONFIG = yaml.safe_load(f) or {}
except FileNotFoundError:
    CONFIG = {}

API_BASE_URL = (os.getenv("API_BASE_URL") or "").rstrip("/")
API_TOKEN = os.getenv("API_TOKEN")

if not API_BASE_URL:
    raise ValueError("API_BASE_URL is not set in .env")
if not API_TOKEN:
    raise ValueError("API_TOKEN is not set in .env")

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

# -----------------------------------------------------------------------------
# Logging / HTTP Session mit Retries
# -----------------------------------------------------------------------------
logger = logging.getLogger("api_client")
logger.setLevel(logging.DEBUG if CONFIG.get("api", {}).get("debug") else logging.INFO)

TIMEOUT = int(CONFIG.get("api", {}).get("timeout_seconds", 20))
RETRIES_CFG = CONFIG.get("api", {}).get("retries", {}) or {}

_session = requests.Session()
retry = Retry(
    total=int(RETRIES_CFG.get("total", 0)),
    read=int(RETRIES_CFG.get("total", 0)),
    connect=int(RETRIES_CFG.get("total", 0)),
    backoff_factor=float(RETRIES_CFG.get("backoff_factor", 0)),
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset({"GET", "POST"}),
)
_adapter = HTTPAdapter(max_retries=retry)
_session.mount("http://", _adapter)
_session.mount("https://", _adapter)
_LAST_ERROR: Optional[str] = None

# -----------------------------------------------------------------------------
# Low-level HTTP
# -----------------------------------------------------------------------------
def _request(method: str, url: str, *, json: Optional[dict] = None, params: Optional[dict] = None) -> requests.Response:
    global _LAST_ERROR
    t0 = time.perf_counter()
    try:
        r = _session.request(method, url, headers=HEADERS, json=json, params=params, timeout=TIMEOUT)
    except Exception as e:
        _LAST_ERROR = f"request-error {method} {url}: {e}"
        if logger.isEnabledFor(logging.DEBUG):
            logger.error(_LAST_ERROR)
        raise

    dt_ms = int((time.perf_counter() - t0) * 1000)
    if logger.isEnabledFor(logging.DEBUG):
        body_preview = (r.text or "")[:400]
        logger.debug(
            "HTTP %s %s → %s in %d ms | resp-bytes=%s | preview=%r",
            method, url, r.status_code, dt_ms, r.headers.get("Content-Length"), body_preview,
        )

    if r.status_code >= 400:
        _LAST_ERROR = f"HTTP {r.status_code} for {url}; body={(r.text or '')[:500]}"
    else:
        _LAST_ERROR = None
    return r

def _get(url: str, params: Optional[dict] = None) -> dict:
    r = _request("GET", url, params=params)
    r.raise_for_status()
    return r.json()

def _post(url: str, json: dict) -> dict:
    r = _request("POST", url, json=json)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {"ok": True}

def get_last_error() -> Optional[str]:
    return _LAST_ERROR

# -----------------------------------------------------------------------------
# API Wrapper
# -----------------------------------------------------------------------------
def get_players() -> List[Dict]:
    try:
        data = _get(f"{API_BASE_URL}/api/get_players")
    except Exception as e:
        print(f"[api_client] get_players() fehlgeschlagen: {e}")
        return []

    result: List[Dict] = []
    for p in data.get("result", []):
        result.append(
            {
                "name": p.get("name"),
                "is_vip": bool(p.get("is_vip")),
                "steam_id_64": p.get("player_id") or p.get("steam_id_64") or p.get("steam_id"),
                "team": p.get("team"),
            }
        )
    return result

def get_detailed_players() -> List[Dict]:
    try:
        raw = _get(f"{API_BASE_URL}/api/get_detailed_players")
    except Exception as e:
        print(f"[api_client] get_detailed_players() fehlgeschlagen: {e}")
        return []

    payload = raw.get("result") or raw.get("data", {}).get("result")
    out: List[Dict] = []
    if not payload:
        return out

    mapping = payload.get("players")
    if isinstance(mapping, dict):
        for steam_id, p in mapping.items():
            out.append({
                "name": p.get("name"),
                "steam_id_64": p.get("player_id") or steam_id,
                "is_vip": bool(p.get("is_vip")),
                "team": (p.get("team") or "").lower() or None,
            })
        return out

    if isinstance(payload, list):
        for p in payload:
            out.append({
                "name": p.get("name"),
                "steam_id_64": p.get("player_id"),
                "is_vip": bool(p.get("is_vip")),
                "team": (p.get("team") or "").lower() or None,
            })
    return out

def message_player(player_name: str, steam_id_64: str, message: str, save_message: bool = True) -> dict:
    payload = {
        "player_name": player_name,
        "player_id": steam_id_64,
        "message": message,
        "save_message": save_message,
    }
    return _post(f"{API_BASE_URL}/api/message_player", json=payload)

def message_all(msg: str) -> dict:
    try:
        players = get_players()
        sent = 0
        errors = 0
        for p in players:
            try:
                message_player(p.get("name"), p.get("steam_id_64"), msg)
                sent += 1
                time.sleep(0.2)
            except Exception:
                errors += 1
                continue
        return {"ok": True, "count": sent, "errors": errors}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def message_side(side: str, msg: str) -> dict:
    try:
        side = (side or "").strip().lower()
        if side not in {"allies", "axis"}:
            return {"ok": False, "error": f"invalid side '{side}'"}

        from_players = get_detailed_players()
        target = [p for p in from_players if (str(p.get("team") or "").lower() == side)]
        if not target:
            return {"ok": False, "error": f"no players on side '{side}'", "count": 0}

        sent = 0
        errors = 0
        for p in target:
            try:
                message_player(p.get("name"), p.get("steam_id_64"), msg)
                sent += 1
                time.sleep(0.2)
            except Exception:
                errors += 1
                continue

        return {"ok": True, "count": sent, "errors": errors}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def set_map(map_name: str) -> dict:
    url = f"{API_BASE_URL}/api/set_map"
    payload = {"map_name": map_name}
    try:
        resp = _session.post(url, json=payload, timeout=TIMEOUT, headers=HEADERS)
        resp.raise_for_status()
        ctype = (resp.headers.get("content-type") or "").lower()
        if ctype.startswith("application/json"):
            data = resp.json()
            if isinstance(data, dict) and "ok" not in data:
                data["ok"] = True
            return data if isinstance(data, dict) else {"ok": True, "data": data}
        return {"ok": True}
    except requests.RequestException as e:
        msg = str(e)
        resp = getattr(e, "response", None)
        if resp is not None:
            msg = f"{e} | status={resp.status_code} | body={(resp.text or '')[:800]} | payload={payload}"
        global _LAST_ERROR
        _LAST_ERROR = msg
        return {"ok": False, "error": msg}

def do_kick_player(player: str, steam_id_64: str, reason: str) -> dict:
    url = f"{API_BASE_URL}/api/kick"
    data = {
        "player_name": player,
        "player_id": steam_id_64,
        "reason": reason,
        "by": "Admin",
    }
    r = _session.post(url, json=data, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def do_punish_player(player_name: str, reason: str, by: str) -> dict:
    url = f"{API_BASE_URL}/api/punish"
    data = {"player_name": player_name, "reason": reason, "by": by}
    r = _session.post(url, json=data, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def do_switch_player_now(player_name: str) -> bool:
    """POST /api/switch_player_now  → bool"""
    url = f"{API_BASE_URL}/api/switch_player_now"
    data = {"player_name": player_name}
    r = _session.post(url, json=data, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    try:
        js = r.json()
        # häufig liefert dein Backend {"result": true, ...}
        if isinstance(js, dict) and "result" in js:
            return bool(js["result"])
    except Exception:
        pass
    # wenn keine JSON-Antwort → 2xx als Erfolg werten
    return True

# -----------------------------------------------------------------------------
# Diagnose / Health
# -----------------------------------------------------------------------------
def _tcp_connectivity_check() -> dict:
    try:
        parts = urlparse(API_BASE_URL)
        host = parts.hostname
        port = parts.port or (443 if parts.scheme == "https" else 80)
        if not host:
            return {"ok": False, "error": "API_BASE_URL hat keinen Host."}
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        t0 = time.perf_counter()
        s.connect((host, port))
        s.close()
        return {"ok": True, "host": host, "port": port, "rtt_ms": int((time.perf_counter() - t0) * 1000)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def try_endpoints(candidates: List[str]) -> dict:
    last = None
    for path in candidates:
        url = f"{API_BASE_URL}{path}"
        try:
            r = _request("GET", url)
            code = r.status_code
            try:
                data = r.json()
            except Exception:
                data = {"text": (r.text or "")[:200]}
            return {"url": url, "status": code, "data": data}
        except Exception as e:
            last = str(e)
    return {"url": None, "status": None, "error": last or "unbekannt"}

def diagnose() -> dict:
    net = _tcp_connectivity_check()
    ver = try_endpoints(["/api/version", "/api/about", "/version", "/health"])
    try:
        data = _get(f"{API_BASE_URL}/api/get_players")
        players = {"status": 200, "count": len(data.get("result", []))}
    except Exception as e:
        players = {"status": "error", "error": str(e)}
    return {
        "api_base_url": API_BASE_URL,
        "timeout_s": TIMEOUT,
        "debug": logger.isEnabledFor(logging.DEBUG),
        "network": net,
        "version": ver,
        "get_players": players,
        "last_error": get_last_error(),
    }

__all__ = [
    "get_players",
    "get_detailed_players",
    "message_player",
    "message_all",
    "message_side",
    "set_map",
    "do_kick_player",
    "do_punish_player",
    "do_switch_player_now",
    "get_last_error",
    "diagnose",
]
