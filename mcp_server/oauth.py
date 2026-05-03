"""
Open Food Ledger OAuth 2.0 provider for the MCP server.

In-memory storage (clients, sessions, auth codes, token cache). Restart
wipes everything; Claude.ai will re-do dynamic client registration on
reconnect, so this is fine for testing.

Access token = the user's api_token from the FastAPI app. The OAuth flow
just exchanges email+password for that token; no separate token universe.
This means:
  - OAuth-obtained tokens validate via the same /api/me check.
  - Tokens revoked via the SPA's "Rotate" button immediately stop working.
  - Direct bearer tokens (no OAuth) keep working — same validation path.
"""
from __future__ import annotations

import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from mcp.server.auth.provider import (
    AccessToken,
    AuthorizationCode,
    AuthorizationParams,
    OAuthAuthorizationServerProvider,
    RefreshToken,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

SESSION_TTL = 600
CODE_TTL = 300
TOKEN_CACHE_TTL = 60


@dataclass
class LoginSession:
    client_id: str
    redirect_uri: str
    redirect_uri_provided_explicitly: bool
    code_challenge: str
    state: str | None
    scopes: list[str]
    resource: str | None
    expires_at: float


class OpenFoodLedgerOAuthProvider(
    OAuthAuthorizationServerProvider[AuthorizationCode, RefreshToken, AccessToken]
):
    """OAuth provider that delegates user auth to the FastAPI app."""

    def __init__(self, api_url: str, public_url: str):
        self.api_url = api_url.rstrip("/")
        self.public_url = public_url.rstrip("/")
        self._clients: dict[str, OAuthClientInformationFull] = {}
        self._sessions: dict[str, LoginSession] = {}
        self._codes: dict[str, tuple[AuthorizationCode, str]] = {}  # code -> (info, api_token)
        self._token_cache: dict[str, float] = {}  # api_token -> verified_until

    # ---- client registry ----

    async def register_client(self, client_info: OAuthClientInformationFull) -> None:
        self._clients[client_info.client_id] = client_info

    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None:
        return self._clients.get(client_id)

    # ---- authorization ----

    async def authorize(
        self,
        client: OAuthClientInformationFull,
        params: AuthorizationParams,
    ) -> str:
        sid = secrets.token_urlsafe(24)
        self._sessions[sid] = LoginSession(
            client_id=client.client_id,
            redirect_uri=str(params.redirect_uri),
            redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
            code_challenge=params.code_challenge,
            state=params.state,
            scopes=params.scopes or [],
            resource=params.resource,
            expires_at=time.time() + SESSION_TTL,
        )
        return f"{self.public_url}/oauth/login?sid={sid}"

    def get_session(self, sid: str) -> LoginSession | None:
        s = self._sessions.get(sid)
        if s is None:
            return None
        if s.expires_at < time.time():
            self._sessions.pop(sid, None)
            return None
        return s

    def consume_session(self, sid: str) -> LoginSession | None:
        s = self.get_session(sid)
        if s is not None:
            self._sessions.pop(sid, None)
        return s

    def issue_code(self, session: LoginSession, api_token: str) -> str:
        code_str = secrets.token_urlsafe(32)
        info = AuthorizationCode(
            code=code_str,
            scopes=session.scopes,
            expires_at=time.time() + CODE_TTL,
            client_id=session.client_id,
            code_challenge=session.code_challenge,
            redirect_uri=session.redirect_uri,  # type: ignore[arg-type]
            redirect_uri_provided_explicitly=session.redirect_uri_provided_explicitly,
            resource=session.resource,
        )
        self._codes[code_str] = (info, api_token)
        return code_str

    async def load_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: str,
    ) -> AuthorizationCode | None:
        entry = self._codes.get(authorization_code)
        if not entry:
            return None
        info, _ = entry
        if info.client_id != client.client_id:
            return None
        if info.expires_at < time.time():
            self._codes.pop(authorization_code, None)
            return None
        return info

    async def exchange_authorization_code(
        self,
        client: OAuthClientInformationFull,
        authorization_code: AuthorizationCode,
    ) -> OAuthToken:
        entry = self._codes.pop(authorization_code.code, None)
        if not entry:
            raise ValueError("authorization code already used or expired")
        _, api_token = entry
        # Access token = the user's api_token. No separate issuance.
        return OAuthToken(
            access_token=api_token,
            token_type="Bearer",
            expires_in=None,
            scope=" ".join(authorization_code.scopes) if authorization_code.scopes else None,
            refresh_token=None,
        )

    # ---- token validation (called on every MCP request) ----

    async def load_access_token(self, token: str) -> AccessToken | None:
        if not token:
            return None
        now = time.time()
        cached_until = self._token_cache.get(token)
        if cached_until and cached_until > now:
            return AccessToken(
                token=token, client_id="(api-token)", scopes=[], expires_at=None
            )
        if not self._verify_via_api(token):
            self._token_cache.pop(token, None)
            return None
        self._token_cache[token] = now + TOKEN_CACHE_TTL
        return AccessToken(
            token=token, client_id="(api-token)", scopes=[], expires_at=None
        )

    def _verify_via_api(self, token: str) -> bool:
        req = urllib.request.Request(
            f"{self.api_url}/api/me",
            method="GET",
            headers={"Authorization": f"Bearer {token}"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return 200 <= resp.status < 300
        except urllib.error.HTTPError:
            return False
        except Exception:
            return False

    # ---- refresh tokens: not supported ----

    async def load_refresh_token(
        self, client: OAuthClientInformationFull, refresh_token: str
    ) -> RefreshToken | None:
        return None

    async def exchange_refresh_token(
        self,
        client: OAuthClientInformationFull,
        refresh_token: RefreshToken,
        scopes: list[str],
    ) -> OAuthToken:
        raise NotImplementedError("refresh tokens are not supported")

    async def revoke_token(self, token) -> None:
        # We can't actually revoke the api_token from here (would need DB).
        # Tell the user to "Rotate" in the SPA. Drop our cache entry at least.
        if isinstance(token, AccessToken):
            self._token_cache.pop(token.token, None)

    # ---- helpers used by login route ----

    def login(self, email: str, password: str) -> str | None:
        """Call the FastAPI /api/auth/login, return api_token on success."""
        body = json.dumps({"email": email, "password": password}).encode()
        req = urllib.request.Request(
            f"{self.api_url}/api/auth/login",
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                return data.get("api_token")
        except Exception:
            return None
