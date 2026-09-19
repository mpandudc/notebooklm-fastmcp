"""
Configuration and settings for notebooklm-fastmcp.
Supports custom notebook aliases and vault paths via environment or JSON config.
"""
from pathlib import Path
from typing import Dict
import os
import json

CONFIG_DIR = Path(os.getenv("NOTEBOOKLM_CONFIG_DIR", Path.home() / ".config" / "notebooklm-fastmcp"))
CONFIG_FILE = CONFIG_DIR / "config.json"
STORAGE_DIR = Path(os.getenv("NOTEBOOKLM_STORAGE_DIR", Path.home() / ".notebooklm"))

# Default Obsidian Vault path
DEFAULT_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", str(Path.home() / "vaults" / "pandu-second-brain"))

def ensure_dirs():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def load_aliases() -> Dict[str, str]:
    """Load user-defined notebook aliases (e.g. {'thesis': 'uuid-1', 'crypto': 'uuid-2'})."""
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            return data.get("aliases", {})
        except Exception:
            return {}
    return {}

def save_alias(alias: str, notebook_id: str):
    """Save or update an alias in user config."""
    ensure_dirs()
    data = {}
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    aliases = data.get("aliases", {})
    aliases[alias.lower().strip()] = notebook_id.strip()
    data["aliases"] = aliases
    CONFIG_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
