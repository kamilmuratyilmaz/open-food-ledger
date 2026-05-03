# OAuth 2.0

The MCP server's HTTP transport supports OAuth 2.0 + PKCE. This is what lets remote MCP connectors talk to your API on your behalf without ever seeing your password.

## Roles

| Role | Who in this app |
|---|---|
| **User** | The person typing email + password in the browser (SPA account holder) |
| **Client** | The remote MCP connector |
| **Authorization Server** | The MCP server (`/authorize`, `/token`, etc.) |
| **Resource Server** | The FastAPI app (`/api/*`) — actual data lives here |

Auth server and resource server happen to run in the same process today; they could be split.

## Flow (Authorization Code + PKCE)

1. The user gives the connector an MCP URL: `https://server/mcp`
2. Connector → `GET /.well-known/oauth-authorization-server` (RFC 8414 metadata discovery)
3. Server responds with `authorization_endpoint`, `token_endpoint`, `registration_endpoint` URLs
4. Connector → `POST /register` (Dynamic Client Registration, RFC 7591) → receives `client_id` + `client_secret`
5. Connector redirects the user to:
   ```
   /authorize?client_id=...&redirect_uri=...&response_type=code
            &code_challenge=<S256 hash>&code_challenge_method=S256
            &state=<random>
   ```
6. Server redirects to `/oauth/login`; the user enters their SPA email + password
7. Server validates against `/api/auth/login`; on success, mints a short-lived **authorization code**
8. Server redirects back to `redirect_uri` with `?code=xxx&state=xxx`
9. Connector → `POST /token` (code + `code_verifier` + `client_secret`) → receives **access_token**
10. The connector sends `Authorization: Bearer <access_token>` on every MCP request
11. Server's `load_access_token` validates the bearer by calling `/api/me`

## Endpoints

| Path | RFC | What it does |
|---|---|---|
| `/.well-known/oauth-authorization-server` | 8414 | Auth server metadata (endpoint list) |
| `/.well-known/oauth-protected-resource` | 9728 | Resource server metadata (which auth server to use) |
| `/register` | 7591 | Dynamic Client Registration |
| `/authorize` | 6749 | Authorization endpoint |
| `/oauth/login` | — | Custom user login form (our addition) |
| `/token` | 6749 | Exchange code for access_token |
| `/revoke` | 7009 | Token revocation |

The `/.well-known/*` endpoints are **not files on disk** — they're Python handlers that produce JSON at runtime. Implementation lives in `mcp/server/auth/routes.py` (vendor package).

## Why PKCE

The authorization code travels back to the client through a redirect URI. That URL can show up in browser history, network proxies, logs. If someone captured the code and POSTed it to `/token`, they'd normally get an access_token.

PKCE blocks that:

1. The connector generates a random `code_verifier`, sends its SHA-256 hash as `code_challenge` to `/authorize`
2. On the `/token` call, the connector sends the original `code_verifier`
3. The server checks `SHA256(verifier) == saved_challenge`

Even if an attacker steals the code, they don't know the `code_verifier` — the code is useless.

`code_challenge_method=S256` is required; we don't accept plain.

## What is the access token

Deliberate shortcut: **access_token = the user's `api_token`**. OAuth is just a wrapper over the existing bearer system, not a new token universe.

Consequences:
- OAuth-issued bearers and directly-pasted bearers go through the same `load_access_token` path
- Hitting "Rotate" in the SPA invalidates all OAuth-bound clients too
- No refresh tokens, `expires_in` is null — the token is long-lived and only goes away when the user rotates

## State storage

The OAuth provider (`mcp_server/oauth.py`) keeps everything in in-memory dicts:

| Stored where? | Why |
|---|---|
| `_clients` (registered connectors) | **In-memory, lost on restart.** A real production setup wants this in a database table. Today: connectors re-register after a restart (usually automatic). |
| `_sessions` (pending login sessions) | In-memory, 10-min TTL — this is enough |
| `_codes` (one-time auth codes) | In-memory, 5-min TTL — used within seconds |
| `_token_cache` (api_token validation cache) | In-memory, 60-sec TTL — performance optimization |

Tokens themselves aren't stored separately because `api_token` is already in the `users` table in Postgres. Validation is per-request via `/api/me` plus the small cache.

## Common errors

**"invalid_client"** — unknown client_id. If the server restarted, the in-memory dict was wiped; the connector should re-register (usually automatic).

**"invalid_grant"** — code already used, expired, or `code_verifier` doesn't match.

**Authorization page redirects to localhost** — `MCP_PUBLIC_URL` is wrong. It should be your real public URL (tunnel URL or production domain).

**Connector won't connect, no error** — check that `.well-known` URLs are reachable from the public internet. HTTPS is required; HTTP isn't accepted.

## TODOs (for production)

- Persist `_clients` and `_codes` in a database (`oauth_clients`, `oauth_codes` tables)
- Add refresh token support
- A real consent screen (login = consent isn't enough; show "X wants the following permissions")
- Scope system (read-only, write, etc.)
- Rate limiting on the login endpoint (brute-force protection)
