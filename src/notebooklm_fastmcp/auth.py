"""
Authentication helper for Google NotebookLM.
Reads credentials from local storage state and handles auth status checks.
"""
from pathlib import Path
from typing import Dict, Any, Tuple
import os
import json
import time

STORAGE_PATH = Path(os.getenv("NOTEBOOKLM_STORAGE_PATH", Path.home() / ".notebooklm" / "profiles" / "default" / "storage_state.json"))

def check_auth_status() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if authentication cookies exist and are not visibly expired.
    Returns (is_valid, message, details).
    """
    if not STORAGE_PATH.exists():
        return False, f"Storage state file not found at {STORAGE_PATH}. Run 'notebooklm auth import-cookies <file>' first.", {}

    try:
        data = json.loads(STORAGE_PATH.read_text(encoding="utf-8"))
        cookies = data.get("cookies", [])
        if not cookies:
            return False, "No cookies found in storage state.", {}

        # Look for critical session cookies
        found = {c.get("name"): c for c in cookies if c.get("name") in ["SID", "__Secure-1PSID", "__Secure-1PSIDTS"]}
        if "SID" not in found and "__Secure-1PSID" not in found:
            return False, "Missing critical SID / __Secure-1PSID cookies.", {}

        psidts = found.get("__Secure-1PSIDTS")
        now = time.time()
        expiry_info = "Unknown"
        if psidts and "expires" in psidts:
            exp = psidts["expires"]
            if isinstance(exp, (int, float)):
                if exp < now:
                    return False, f"Session cookie __Secure-1PSIDTS expired at {time.ctime(exp)}.", {}
                expiry_info = time.ctime(exp)

        return True, "Authenticated", {
            "storage_path": str(STORAGE_PATH),
            "cookie_count": len(cookies),
            "psidts_expires": expiry_info
        }
    except Exception as e:
        return False, f"Error parsing credentials: {e}", {}
