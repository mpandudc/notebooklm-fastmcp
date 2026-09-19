# notebooklm-fastmcp

A lean, production-ready **FastMCP** (Model Context Protocol) server for **Google NotebookLM**, engineered for AI agents (Hermes, Claude Desktop, Cursor, Roo-Code) with native **Obsidian Second Brain** Markdown sync and long-lived **Google Master Token (AAS)** support.

Unlike bloated community implementations that dump 40+ low-level endpoints into your LLM context window, `notebooklm-fastmcp` exposes only **8 high-signal, high-leverage tools** and provides seamless export into bidirectional `[[wikilinks]]` Markdown vaults.

---

## 🌟 Key Features

* **Lean Context-Efficient Tool Surface:** 8 curated tools (saving ~80% context window token overhead vs upstream).
* **Robust Multi-Method Auth:** Supports standard browser cookies AND long-lived Google Master Token (AAS) with auto-reminting.
* **Proactive Expiration Webhook:** Sends webhook alerts (Telegram, Discord, Slack) when session cookies expire.
* **1-Shot Audio Deep Dive (Podcast Duo):** Generate and download full `.mp3` podcasts with a single tool call.
* **Dual Transport:** Runs via standard `stdio` or as a background **SSE HTTP daemon** for multi-agent shared access.
* **Direct Obsidian Second Brain Bridge:** Saves grounded research notes directly to your local Markdown vault with YAML frontmatter, tags, and `[[wikilinks]]`.
* **Dynamic Notebook Aliasing:** Map cumbersome Google UUIDs (e.g. `9823f-123...`) to human-readable names like `crypto`, `thesis`, or `fintech`.

---

## 🛠️ Tool Catalog (8 Tools)

1. **`notebook_ask`**: Ask grounded questions against notebook sources with precise citations.
2. **`notebook_create`**: Create a new NotebookLM workspace and optionally assign a shortcut alias.
3. **`notebook_list_sources`**: List all uploaded documents/sources in a given notebook.
4. **`notebook_ingest_url`**: Upload web articles, research papers, or YouTube URLs directly as sources.
5. **`notebook_ingest_file`**: Upload local PDFs, docs, or text files into any notebook.
6. **`notebook_generate_podcast`**: 1-shot generate and download AI host audio deep dive (`.mp3`).
7. **`notebook_sync_to_vault`**: Run grounded research and automatically compile it into Obsidian-compliant Markdown notes.
8. **`notebook_alias_manage`**: List or register user-friendly notebook aliases (`action: 'list' | 'set'`).
9. **`notebook_status`**: Diagnostic check for Google session validity, master token status, active aliases, and vault paths.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/mpandudc/notebooklm-fastmcp.git
cd notebooklm-fastmcp

# Install via uv (recommended)
uv sync
```

### 2. Authentication Options

#### Option A: Browser Cookies (Standard)
Export cookies from `notebooklm.google.com` (using Cookie-Editor extension) into JSON format:
```bash
mkdir -p ~/.notebooklm/profiles/default/
# Save cookies as: ~/.notebooklm/profiles/default/storage_state.json
```

#### Option B: Google Master Token / AAS (Self-Healing / Long-Lived)
If you have a Google Master Token (`oauth_token` / AAS token from Android auth):
```bash
# Save as: ~/.notebooklm/profiles/default/master_token.json
# The server will automatically remint expired cookies without user intervention.
```

---

## ⚙️ Configuration & Agent Integration

### Claude Desktop / Hermes / Cursor MCP Setup

#### Option A: Local `stdio`
```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/notebooklm-fastmcp", "notebooklm-fastmcp", "--transport", "stdio"]
    }
  }
}
```

#### Option B: SSE Daemon (Multi-Agent Shared Server)
Run the server as a systemd service or background daemon on port `8766`:
```bash
uv run notebooklm-fastmcp --transport sse --port 8766
```

Then point your agents to:
```yaml
mcp_servers:
  notebooklm:
    url: http://127.0.0.1:8766/sse
    transport: sse
    enabled: true
```

---

## 📝 Environment Variables

* `NOTEBOOKLM_STORAGE_PATH`: Path to `storage_state.json` (Default: `~/.notebooklm/profiles/default/storage_state.json`).
* `NOTEBOOKLM_MASTER_TOKEN_PATH`: Path to `master_token.json` (Default: `~/.notebooklm/profiles/default/master_token.json`).
* `NOTEBOOKLM_AUTH_ALERT_WEBHOOK`: Webhook URL to alert when session expires (Telegram / Discord webhook).
* `OBSIDIAN_VAULT_PATH`: Absolute path to your Obsidian vault root (Default: `~/vaults/pandu-second-brain`).
* `NOTEBOOKLM_CONFIG_DIR`: Path to custom aliases config (Default: `~/.config/notebooklm-fastmcp`).

---

## 📄 License

MIT License. Crafted for high-signal autonomous research workflows.
