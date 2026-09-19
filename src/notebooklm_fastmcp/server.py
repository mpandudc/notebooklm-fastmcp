"""
FastMCP Server for Google NotebookLM.
Exposes lean, high-signal tools for AI Agents and Second Brain sync.
"""
from fastmcp import FastMCP
from typing import Optional, Dict, Any, List
from pathlib import Path
import os
import sys
import asyncio

from .config import load_aliases, save_alias, DEFAULT_VAULT_PATH
from .auth import check_auth_status, auto_remint_if_available, send_expiry_alert, STORAGE_PATH
from .vault_sync import format_obsidian_note, write_to_vault

mcp = FastMCP("notebooklm-fastmcp")

def _resolve_notebook_id(target: str) -> str:
    """Resolve an alias (e.g. 'crypto', 'thesis') or return raw notebook UUID."""
    aliases = load_aliases()
    target_clean = target.lower().strip()
    if target_clean in aliases:
        return aliases[target_clean]
    return target.strip()

async def _ensure_auth() -> tuple[bool, str]:
    """Check auth and attempt auto-reminting if expired."""
    is_valid, msg, details = check_auth_status()
    if not is_valid:
        reminted = await auto_remint_if_available()
        if reminted:
            is_valid, msg, details = check_auth_status()
            if is_valid:
                return True, "Auto-reminted successfully"

        await send_expiry_alert(msg)
        return False, msg
    return True, "Authenticated"

@mcp.tool()
async def notebook_status() -> Dict[str, Any]:
    """
    Check connection health, authentication status, and active aliases of NotebookLM.
    """
    is_valid, msg, details = check_auth_status()
    aliases = load_aliases()
    return {
        "authenticated": is_valid,
        "message": msg,
        "details": details,
        "registered_aliases": aliases,
        "default_vault_path": DEFAULT_VAULT_PATH
    }

@mcp.tool()
def notebook_alias_manage(action: str, alias: str = "", notebook_id: str = "") -> str:
    """
    Manage user-friendly notebook aliases.
    action: 'list' | 'set'
    alias: name shortcut (e.g. 'thesis', 'fintech')
    notebook_id: Google NotebookLM UUID
    """
    action = action.lower().strip()
    if action == "list":
        aliases = load_aliases()
        if not aliases:
            return "No aliases registered yet. Use action='set' to create one."
        return "\n".join([f"- **{k}**: `{v}`" for k, v in aliases.items()])
    elif action == "set":
        if not alias or not notebook_id:
            return "Error: Both 'alias' and 'notebook_id' are required to set an alias."
        save_alias(alias, notebook_id)
        return f"Alias saved: **{alias}** -> `{notebook_id}`"
    else:
        return f"Unknown action '{action}'. Allowed actions: 'list', 'set'."

@mcp.tool()
async def notebook_create(title: str, alias: Optional[str] = None) -> str:
    """
    Create a new NotebookLM workspace and optionally assign it a shortcut alias.
    """
    ok, msg = await _ensure_auth()
    if not ok:
        return f"AUTH_ERROR: {msg}"

    try:
        from notebooklm.client import NotebookLMClient
        async with NotebookLMClient.from_storage(path=str(STORAGE_PATH)) as client:
            nb = await client.notebooks.create(title=title)
            nb_id = getattr(nb, "id", str(nb))
            alias_note = ""
            if alias:
                save_alias(alias, nb_id)
                alias_note = f" (Alias registered: `{alias}`)"
            return f"Successfully created notebook '{title}' [ID: `{nb_id}`]{alias_note}"
    except Exception as e:
        return f"Error creating notebook: {e}"

@mcp.tool()
async def notebook_list_sources(notebook: str) -> str:
    """
    List all uploaded sources and documents in a given notebook.
    notebook: alias name or full Notebook UUID.
    """
    notebook_id = _resolve_notebook_id(notebook)
    if not notebook_id:
        return f"Error: Could not resolve notebook '{notebook}'."

    ok, msg = await _ensure_auth()
    if not ok:
        return f"AUTH_ERROR: {msg}"

    try:
        from notebooklm.client import NotebookLMClient
        async with NotebookLMClient.from_storage(path=str(STORAGE_PATH)) as client:
            sources = await client.sources.list(notebook_id=notebook_id)
            if not sources:
                return f"Notebook `{notebook_id}` has no sources yet."
            lines = [f"- **{getattr(s, 'title', 'Untitled')}** (`{getattr(s, 'id', 'unknown')}`)" for s in sources]
            return f"### Sources in Notebook (`{notebook}`):\n" + "\n".join(lines)
    except Exception as e:
        return f"Error listing sources: {e}"

@mcp.tool()
async def notebook_ask(
    query: str,
    notebook: str,
    conversation_id: Optional[str] = None
) -> str:
    """
    Ask a question grounded against sources in a Google NotebookLM notebook.
    notebook: alias name (e.g. 'thesis') or full Notebook UUID.
    """
    notebook_id = _resolve_notebook_id(notebook)
    if not notebook_id:
        return f"Error: Could not resolve notebook '{notebook}'. Provide an alias or UUID."

    ok, msg = await _ensure_auth()
    if not ok:
        return f"AUTH_ERROR: {msg}. Please re-import Google cookies or master token."

    try:
        from notebooklm.client import NotebookLMClient
        async with NotebookLMClient.from_storage(path=str(STORAGE_PATH)) as client:
            result = await client.chat.ask(notebook_id=notebook_id, question=query, conversation_id=conversation_id)
            answer = getattr(result, "text", str(result))
            references = getattr(result, "references", []) or getattr(result, "citations", [])
            
            cit_str = ""
            if references:
                cit_str = "\n\n**Citations:**\n" + "\n".join([f"- {r}" for r in references])
            return f"{answer}{cit_str}"
    except Exception as e:
        return f"Error querying NotebookLM: {e}"

@mcp.tool()
async def notebook_ingest_url(
    url: str,
    notebook: str
) -> str:
    """
    Ingest a web URL or YouTube link as a source into a NotebookLM notebook.
    notebook: alias name or full Notebook UUID.
    """
    notebook_id = _resolve_notebook_id(notebook)
    if not notebook_id:
        return f"Error: Could not resolve notebook '{notebook}'."

    ok, msg = await _ensure_auth()
    if not ok:
        return f"AUTH_ERROR: {msg}."

    try:
        from notebooklm.client import NotebookLMClient
        async with NotebookLMClient.from_storage(path=str(STORAGE_PATH)) as client:
            await client.sources.add_url(notebook_id=notebook_id, url=url)
            return f"Successfully added source URL to notebook `{notebook_id}`: {url}"
    except Exception as e:
        return f"Error ingesting URL into NotebookLM: {e}"

@mcp.tool()
async def notebook_ingest_file(
    file_path: str,
    notebook: str
) -> str:
    """
    Upload a local document (PDF, docx, txt, markdown) into a NotebookLM notebook.
    notebook: alias name or full Notebook UUID.
    """
    notebook_id = _resolve_notebook_id(notebook)
    if not notebook_id:
        return f"Error: Could not resolve notebook '{notebook}'."

    path = Path(file_path).resolve()
    if not path.exists():
        return f"Error: File '{file_path}' does not exist."

    ok, msg = await _ensure_auth()
    if not ok:
        return f"AUTH_ERROR: {msg}."

    try:
        from notebooklm.client import NotebookLMClient
        async with NotebookLMClient.from_storage(path=str(STORAGE_PATH)) as client:
            await client.sources.add_file(notebook_id=notebook_id, file_path=path)
            return f"Successfully uploaded '{path.name}' to notebook `{notebook_id}`."
    except Exception as e:
        return f"Error uploading file into NotebookLM: {e}"

@mcp.tool()
async def notebook_generate_podcast(
    notebook: str,
    instructions: Optional[str] = None,
    output_dir: str = "~/Downloads"
) -> str:
    """
    1-Shot Audio Deep Dive (Podcast Duo) generator and downloader.
    Generates AI conversation podcast from sources and saves the .mp3 file locally.
    notebook: alias name or full Notebook UUID.
    instructions: optional customization (e.g. 'Focus on market dynamics and risk').
    output_dir: directory to save the completed MP3 file.
    """
    notebook_id = _resolve_notebook_id(notebook)
    if not notebook_id:
        return f"Error: Could not resolve notebook '{notebook}'."

    ok, msg = await _ensure_auth()
    if not ok:
        return f"AUTH_ERROR: {msg}."

    try:
        from notebooklm.client import NotebookLMClient
        async with NotebookLMClient.from_storage(path=str(STORAGE_PATH)) as client:
            status = await client.artifacts.generate_audio(
                notebook_id=notebook_id,
                instructions=instructions
            )
            task_id = getattr(status, "task_id", None)
            if not task_id:
                return "Error: Failed to obtain generation task_id."

            out_path = Path(output_dir).expanduser().resolve()
            out_path.mkdir(parents=True, exist_ok=True)
            mp3_file = out_path / f"podcast_{notebook_id[:8]}.mp3"

            await client.artifacts.wait_for_completion(notebook_id=notebook_id, task_id=task_id)
            saved_path = await client.artifacts.download_audio(notebook_id=notebook_id, output_path=str(mp3_file))
            return f"Podcast generated and downloaded successfully: `{saved_path}`"
    except Exception as e:
        return f"Error in podcast generation pipeline: {e}"

@mcp.tool()
async def notebook_sync_to_vault(
    query_or_topic: str,
    notebook: str,
    note_title: str,
    folder: str = "resources/notebooklm",
    tags: str = "notebooklm, research"
) -> str:
    """
    Query NotebookLM and automatically save the grounded research note into Obsidian Vault format with [[wikilinks]].
    notebook: alias name or full Notebook UUID.
    note_title: title for the created markdown file.
    folder: relative folder inside the Obsidian vault.
    tags: comma-separated tags.
    """
    notebook_id = _resolve_notebook_id(notebook)
    if not notebook_id:
        return f"Error: Could not resolve notebook '{notebook}'."

    content = await notebook_ask(query=query_or_topic, notebook=notebook)
    if content.startswith("AUTH_ERROR") or content.startswith("Error"):
        return f"Failed to generate content: {content}"

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    safe_filename = "".join([c if c.isalnum() or c in " -_" else "_" for c in note_title]).strip()
    rel_path = f"{folder.strip('/')}/{safe_filename}.md"

    md_content = format_obsidian_note(
        title=note_title,
        content=content,
        notebook_title=notebook,
        notebook_id=notebook_id,
        tags=tag_list
    )

    try:
        saved_file = write_to_vault(DEFAULT_VAULT_PATH, rel_path, md_content)
        return f"Successfully synced research note to Obsidian Vault at: `{saved_file}`"
    except Exception as e:
        return f"Error writing note to vault: {e}"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="NotebookLM FastMCP Server")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], help="Transport type (stdio or sse)")
    parser.add_argument("--port", type=int, default=8766, help="Port for SSE transport")
    parser.add_argument("--host", default="0.0.0.0", help="Host for SSE transport")
    args = parser.parse_args()

    if args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
