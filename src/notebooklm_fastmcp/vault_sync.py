"""
Sync module: exports NotebookLM summaries, answers, or notes into Obsidian Vault format.
Ensures clean YAML frontmatter, tags, and bidirectional [[wikilinks]].
"""
from pathlib import Path
from typing import Dict, Any, Optional
import os
import re
from datetime import datetime

def format_obsidian_note(
    title: str,
    content: str,
    notebook_title: str,
    notebook_id: str,
    tags: Optional[list] = None,
    citations: Optional[list] = None
) -> str:
    """Formats content into standard Obsidian Markdown with YAML frontmatter."""
    tags_list = tags or ["notebooklm", "research"]
    tags_str = "\n".join([f"  - {t}" for t in tags_list])
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    citations_block = ""
    if citations:
        citations_block = "\n\n### 📚 Sources & Citations\n" + "\n".join([f"- {c}" for c in citations])

    frontmatter = f"""---
title: "{title}"
date: {date_str}
type: research-note
source: google-notebooklm
notebook: "[[{notebook_title}]]"
notebook_id: "{notebook_id}"
tags:
{tags_str}
---

# {title}

{content}
{citations_block}
"""
    return frontmatter

def write_to_vault(
    vault_path: str,
    rel_path: str,
    content: str
) -> Path:
    """Writes a note safely into the target Obsidian Vault folder."""
    base = Path(vault_path).resolve()
    target = (base / rel_path).resolve()

    if not str(target).startswith(str(base)):
        raise ValueError(f"Directory traversal detected: {rel_path}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
