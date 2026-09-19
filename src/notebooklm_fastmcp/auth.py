"""
Authentication manager for Google NotebookLM.
Supports:
1. Browser Cookie storage_state.json (Standard)
2. Google Master Token (Long-lived AAS token auto-reminting)
3. Auto-reminting via refresh hooks
4. Telegram / Webhook notification on session expiration
"""
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import os
import json
import time
import httpx

STORAGE_PATH = Path(os.getenv("NOTEBOOKLM_STORAGE_PATH", Path.home() / ".notebooklm" / "profiles" / "default" / "storage_state.json"))
MASTER_TOKEN_PATH = Path(os.getenv("NOTEBOOKLM_MASTER_TOKEN_PATH", Path.home() / ".notebooklm" / "profiles" / "default" / "master_token.json"))

def get_webhook_url() -> Optional[str]:
    """Optional webhook URL to alert when auth expires."""
    return os.getenv("NOTEBOOKLM_AUTH_ALERT_WEBHOOK")

async def send_expiry_alert(reason: str):
    """Notify user via webhook if session expires."""
    url = get_webhook_url()
    if not url:
        return
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "event": "notebooklm_auth_expired",
                "timestamp": time.time(),
                "reason": reason,
                "message": "Google NotebookLM session has expired. Please re-authenticate."
            }
            await client.post(url, json=payload)
    except Exception:
        pass

async def auto_remint_if_available() -> bool:
    """
    Attempt to automatically refresh/remint session cookies using Google Master Token (AAS).
    Returns True if reminting succeeded.
    """
    if not MASTER_TOKEN_PATH.exists():
        return False

    try:
        from notebooklm._auth.master_token import remint_from_stored_token
        await remint_from_stored_token(STORAGE_PATH)
        return True
    except Exception:
        return False

def check_auth_status() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if authentication exists and is valid.
    Returns (is_valid, message, details).
    """
    has_master_token = MASTER_TOKEN_PATH.exists()

    if not STORAGE_PATH.exists():
        if has_master_token:
            return False, "Cookies absent, but Master Token is present. Reminting needed.", {"has_master_token": True}
        return False, f"Credentials not found at {STORAGE_PATH}. Please provide cookies or Google Master Token.", {}

    try:
        data = json.loads(STORAGE_PATH.read_text(encoding="utf-8"))
        cookies = data.get("cookies", [])
        if not cookies:
            return False, "No cookies found in storage state.", {"has_master_token": has_master_token}

        found = {c.get("name"): c for c in cookies if c.get("name") in ["SID", "__Secure-1PSID", "__Secure-1PSIDTS"]}
        if "SID" not in found and "__Secure-1PSID" not in found:
            return False, "Missing critical SID / __Secure-1PSID cookies.", {"has_master_token": has_master_token}

        psidts = found.get("__Secure-1PSIDTS")
        now = time.time()
        expiry_info = "Unknown"
        if psidts and "expires" in psidts:
            exp = psidts["expires"]
            if isinstance(exp, (int, float)):
                if exp < now:
                    return False, f"Session cookie __Secure-1PSIDTS expired at {time.ctime(exp)}.", {
                        "has_master_token": has_master_token,
                        "expired_at": exp
                    }
                expiry_info = time.ctime(exp)

        return True, "Authenticated", {
            "storage_path": str(STORAGE_PATH),
            "cookie_count": len(cookies),
            "psidts_expires": expiry_info,
            "has_master_token": has_master_token
        }
    except Exception as e:
        return False, f"Error parsing credentials: {e}", {"has_master_token": has_master_token}
