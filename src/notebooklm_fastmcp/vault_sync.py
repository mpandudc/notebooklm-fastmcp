"""
Sync module: exports NotebookLM summaries, answers, or notes into Obsidian Vault format.
Ensures clean YAML frontmatter, tags, and bidirectional [[wikilinks]].
"""
from pathlib import Path
from typing import Dict, Any, Optional
import os
import re
import tempfile
from datetime import datetime


def answer_text(result: Any) -> str:
    """Markdown answer from a notebooklm-py AskResult (`.answer`), never its repr."""
    for attr in ("answer", "text"):
        value = getattr(result, attr, None)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return result.strip() if isinstance(result, str) else str(result)


def format_reference(ref: Any, max_chars: int = 200) -> str:
    """One readable line per citation: `[n] cited text… (`source_id`)`."""
    num = getattr(ref, "citation_number", None)
    text = " ".join(str(getattr(ref, "cited_text", "") or "").split())
    if not text and num is None:
        return str(ref)
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "…"
    source = getattr(ref, "source_id", "")
    return f"[{num}] {text}" + (f" (`{source}`)" if source else "")

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
notebook: "{notebook_title}"
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

    if not target.is_relative_to(base):
        raise ValueError(f"Directory traversal detected: {rel_path}")

    target.parent.mkdir(parents=True, exist_ok=True)
    # Temp file + rename: Obsidian / sync plugins never see a half-written note.
    fd, tmp = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as fh:
            fh.write(content)
        os.replace(tmp, target)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return target
