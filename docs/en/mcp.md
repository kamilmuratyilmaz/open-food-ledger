# MCP Server

The MCP server lets AI assistants read and write to your food log. It supports two transports:

- **stdio** — local clients (Claude Desktop, Claude Code) launch it as a subprocess
- **streamable HTTP** — remote clients connect over HTTP

## Tools

| Tool | What it does |
|---|---|
| `log_food` | Add a food entry (food_name, weight_g, meal_type, macros) |
| `list_entries` | List entries with filters (date, meal, name search) |
| `get_recent_meals` | Return the most recent N entries |
| `update_entry` | Edit an existing entry |
| `delete_entry` | Delete an entry |
| `get_daily_totals` | Total macro+micro values for a day (with per-meal breakdown) |
| `get_date_range_summary` | Range summary + per-day averages |
| `analyze_macros` | Macro distribution (4/4/9 kcal/g) + target adherence percentages |
| `find_food` | Substring search by food name across history |
| `suggest_next_meal` | Most frequently eaten foods for a meal type over the last 30 days |

## A) Local setup (stdio)

Local clients (Claude Desktop, Claude Code) run on your machine. The MCP server is launched as a Python subprocess and speaks JSON-RPC over stdin/stdout.

### Setup

1. Install the `mcp` package into your Python environment:
   ```bash
   pip install mcp
   ```

2. In the SPA, create an account and copy your token from **Settings → MCP token → Reveal → Copy**.

3. Add to your client config:

   **Claude Code (project scope):** `.mcp.json` at the project root
   **Claude Desktop:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows) / `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)

   ```json
   {
     "mcpServers": {
       "open-food-ledger": {
         "command": "/absolute/path/to/python",
         "args": ["-m", "mcp_server.server"],
         "cwd": "/absolute/path/to/open-food-ledger",
         "env": {
           "FOOD_API_URL": "http://localhost:8000",
           "FOOD_API_TOKEN": "<token from the SPA>"
         }
       }
     }
   }
   ```

   The `cwd` field is needed so `python -m mcp_server.server` can find the `mcp_server` package. If your client doesn't support `cwd`, the direct path version also works (`server.py` has a sys.path injection that handles it):
   ```json
   "args": ["/absolute/path/to/open-food-ledger/mcp_server/server.py"]
   ```

4. Restart the client. The tools should appear in the list.

### Flow

Client → spawns the MCP server as a subprocess → server uses `FOOD_API_TOKEN` to call FastAPI with bearer auth → tools are invoked over JSON-RPC.

This is a single-user setup: whoever owns the env-var token is whose log gets written.

## B) Remote setup (HTTP + OAuth)

Remote MCP clients can't spawn subprocesses, so they connect over HTTP. In this mode each user signs in with their own account via OAuth 2.0.

### Start the server

```bash
export MCP_TRANSPORT=http
export MCP_PORT=8001                              # optional, default 8001
export MCP_PUBLIC_URL=https://your-domain.example  # required, used in OAuth metadata
export FOOD_API_URL=http://localhost:8000          # where the API is reachable
python -m mcp_server.server                        # run from the project root
```

Endpoint: `https://your-domain.example/mcp`

### Use it in a connector

1. In the connector dialog, set the URL to `https://your-domain.example/mcp`
2. Leave the OAuth Client ID / Secret fields **empty** — Dynamic Client Registration is enabled, the connector will register itself
3. Connect
4. A browser opens → **sign in with your SPA account** → an authorization code is issued → the connector completes the handshake
5. Tools appear

### Local testing (tunnel)

If you're testing locally you'll need a public HTTPS URL — remote MCP clients can't reach `localhost`. Use a tunnel service that gives you an HTTPS URL pointing at port 8001, then put that URL in `MCP_PUBLIC_URL` and restart the server.

### Manual testing with MCP Inspector

For a browser-based tool that lets you exercise the tools manually:

```bash
npx @modelcontextprotocol/inspector
```

Set the URL to `http://localhost:8001/mcp` and add an `Authorization: Bearer <api_token>` header. This connects directly with a bearer, no OAuth handshake needed.

## Auth mode summary

How the MCP server validates bearers:

- **stdio:** reads `FOOD_API_TOKEN` from env, single-user
- **HTTP + OAuth:** reads `Authorization: Bearer` from each request, multi-user
- **HTTP + direct bearer:** even with OAuth enabled, a client can send a bearer directly; it's validated against `/api/me` (Inspector, ChatGPT bearer mode, etc.)

OAuth details: [oauth.md](oauth.md)

## Common errors

**"FOOD_API_TOKEN env değişkenini ayarla"** — stdio mode without a token in env. Check your config's `env` block.

**"406 Not Acceptable"** — a GET hit the HTTP endpoint without `text/event-stream` in `Accept`. Normal — real MCP clients send the right header.

**"Invalid token"** — the bearer is invalid or has been rotated. Get a fresh token from the SPA.

**Browser login page doesn't open (remote mode)** — `MCP_PUBLIC_URL` is unset or wrong. The connector may be redirecting to localhost; check the logs.
