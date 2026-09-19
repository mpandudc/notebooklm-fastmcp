# notebooklm-fastmcp

A lean, production-ready **FastMCP** (Model Context Protocol) server for **Google NotebookLM**, engineered for AI agents (Hermes, Claude Desktop, Cursor, Roo-Code) with native **Obsidian Second Brain** Markdown sync.

Unlike bloated community implementations that dump 40+ low-level endpoints into your LLM context window, `notebooklm-fastmcp` exposes only **6 high-signal, high-leverage tools** and provides seamless export into bidirectional `[[wikilinks]]` Markdown vaults.

---

## 🌟 Key Features

* **Lean Context-Efficient Tool Surface:** Only 6 curated tools (saving ~80% context window token overhead vs upstream).
* **Dual Transport:** Runs via standard `stdio` or as a background **SSE HTTP daemon** for multi-agent shared access.
* **Direct Obsidian Second Brain Bridge:** Saves grounded research notes directly to your local Markdown vault with YAML frontmatter, tags, and `[[wikilinks]]`.
* **Dynamic Notebook Aliasing:** Map cumbersome Google UUIDs (e.g. `9823f-123...`) to human-readable names like `crypto`, `thesis`, or `fintech`.
* **Resilient Authentication & Status Diagnostics:** Built-in cookie expiration detection and non-blocking diagnostic reports.

---

## 🛠️ Tool Catalog (6 Tools)

1. **`notebook_ask`**: Ask grounded questions against notebook sources with precise citations.
2. **`notebook_ingest_url`**: Upload web articles, research papers, or YouTube URLs directly as sources.
3. **`notebook_ingest_file`**: Upload local PDFs, docs, or text files into any notebook.
4. **`notebook_sync_to_vault`**: Run grounded research and automatically compile it into Obsidian-compliant Markdown notes.
5. **`notebook_alias_manage`**: List or register user-friendly notebook aliases (`action: 'list' | 'set'`).
6. **`notebook_status`**: Diagnostic check for Google session validity, active aliases, and vault paths.

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

### 2. Authentication

Export your Google session cookies from your browser (using Cookie-Editor extension on `notebooklm.google.com`) into JSON format, and save them:

```bash
# Place cookies in standard location:
mkdir -p ~/.notebooklm/profiles/default/
# Save cookies as: ~/.notebooklm/profiles/default/storage_state.json
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
* `OBSIDIAN_VAULT_PATH`: Absolute path to your Obsidian vault root (Default: `~/vaults/pandu-second-brain`).
* `NOTEBOOKLM_CONFIG_DIR`: Path to custom aliases config (Default: `~/.config/notebooklm-fastmcp`).

---

## 📄 License

MIT License. Crafted for high-signal autonomous research workflows.
