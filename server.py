"""
Food Tracker MCP Server
=======================

Web app'e HTTP üzerinden bağlanır. Kullanıcı SPA'ya kayıt olur, ayarlar
panelinden API token'ını kopyalar, MCP server'ı bu token ile çalıştırır.

Çalıştır:
    # stdio (Claude Code / Claude Desktop için, default)
    export FOOD_API_URL="http://localhost:8000"
    export FOOD_API_TOKEN="<settings panelinden kopyalanan token>"
    python server.py

    # streamable HTTP (ChatGPT ve uzak client'lar için)
    MCP_TRANSPORT=http MCP_PORT=8001 python server.py
    # → http://localhost:8001/mcp adresinde dinler
"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
import urllib.error
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

API_URL = os.environ.get("FOOD_API_URL", "http://localhost:8000").rstrip("/")
API_TOKEN = os.environ.get("FOOD_API_TOKEN")
TRANSPORT = os.environ.get("MCP_TRANSPORT", "stdio").lower()
HTTP_PORT = int(os.environ.get("MCP_PORT", "8001"))
PUBLIC_URL = os.environ.get("MCP_PUBLIC_URL", f"http://localhost:{HTTP_PORT}").rstrip("/")
OAUTH_ENABLED = TRANSPORT == "http" and os.environ.get("MCP_OAUTH", "1") != "0"

# stdio modunda env'den token şart (tek kullanıcılı, local Claude Desktop/Code).
# HTTP modunda her istek kendi Authorization header'ını taşır — env opsiyonel.
if TRANSPORT == "stdio" and not API_TOKEN:
    raise RuntimeError(
        "FOOD_API_TOKEN env değişkenini ayarla. SPA'da Settings → MCP token "
        "panelinden kopyalayabilirsin."
    )

if OAUTH_ENABLED:
    from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
    from oauth import FoodTrackerOAuthProvider

    _oauth_provider = FoodTrackerOAuthProvider(api_url=API_URL, public_url=PUBLIC_URL)
    mcp = FastMCP(
        "food-tracker",
        host="0.0.0.0",
        port=HTTP_PORT,
        auth_server_provider=_oauth_provider,
        auth=AuthSettings(
            issuer_url=PUBLIC_URL,  # type: ignore[arg-type]
            resource_server_url=PUBLIC_URL,  # type: ignore[arg-type]
            client_registration_options=ClientRegistrationOptions(enabled=True),
            revocation_options=RevocationOptions(enabled=True),
        ),
    )
elif TRANSPORT == "http":
    _oauth_provider = None
    mcp = FastMCP("food-tracker", host="0.0.0.0", port=HTTP_PORT)
else:
    _oauth_provider = None
    mcp = FastMCP("food-tracker")


if OAUTH_ENABLED:
    from html import escape as _html_escape
    from starlette.requests import Request as _StarletteRequest
    from starlette.responses import HTMLResponse, RedirectResponse, PlainTextResponse

    def _render_login(sid: str, error: str | None = None) -> HTMLResponse:
        err_html = f'<p class="err">{_html_escape(error)}</p>' if error else ""
        body = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Food Tracker — Sign in</title>
<style>
  body {{ font-family: system-ui, sans-serif; background:#0e0e10; color:#eee;
         display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0 }}
  form {{ background:#1a1a1f; padding:32px; border-radius:12px; min-width:320px;
         box-shadow:0 12px 40px rgba(0,0,0,0.4) }}
  h1 {{ margin:0 0 4px; font-size:18px }}
  p.sub {{ margin:0 0 20px; color:#888; font-size:13px }}
  label {{ display:block; font-size:12px; color:#aaa; margin:12px 0 4px }}
  input {{ width:100%; box-sizing:border-box; padding:9px 11px; border:1px solid #333;
          background:#0e0e10; color:#eee; border-radius:6px; font-size:14px }}
  button {{ width:100%; margin-top:18px; padding:10px; background:#7857ff; color:#fff;
           border:0; border-radius:6px; font-size:14px; font-weight:600; cursor:pointer }}
  .err {{ color:#ff7070; font-size:13px; margin:0 0 -4px }}
</style></head>
<body><form method="POST" action="/oauth/login">
  <h1>Food Tracker</h1>
  <p class="sub">Sign in to authorize the connector</p>
  {err_html}
  <input type="hidden" name="sid" value="{_html_escape(sid)}" />
  <label>Email</label>
  <input name="email" type="email" required autofocus />
  <label>Password</label>
  <input name="password" type="password" required minlength="8" />
  <button type="submit">Sign in & authorize</button>
</form></body></html>"""
        return HTMLResponse(body)

    @mcp.custom_route("/oauth/login", methods=["GET"])
    async def oauth_login_get(request: _StarletteRequest):
        sid = request.query_params.get("sid", "")
        if not _oauth_provider.get_session(sid):
            return PlainTextResponse(
                "This authorization session has expired or is invalid.",
                status_code=400,
            )
        return _render_login(sid)

    @mcp.custom_route("/oauth/login", methods=["POST"])
    async def oauth_login_post(request: _StarletteRequest):
        form = await request.form()
        sid = str(form.get("sid", ""))
        email = str(form.get("email", "")).strip()
        password = str(form.get("password", ""))
        session = _oauth_provider.get_session(sid)
        if not session:
            return PlainTextResponse("Session expired.", status_code=400)
        if not email or not password:
            return _render_login(sid, error="Email and password required.")
        api_token = _oauth_provider.login(email, password)
        if not api_token:
            return _render_login(sid, error="Invalid email or password.")
        # consume session, issue code, redirect to the client's redirect_uri
        session = _oauth_provider.consume_session(sid)
        code = _oauth_provider.issue_code(session, api_token)
        from urllib.parse import urlencode
        params = {"code": code}
        if session.state:
            params["state"] = session.state
        sep = "&" if "?" in session.redirect_uri else "?"
        return RedirectResponse(
            url=f"{session.redirect_uri}{sep}{urlencode(params)}",
            status_code=302,
        )


def _resolve_token() -> str:
    """Geçerli isteğin Authorization header'ından bearer token'ı çıkar;
    HTTP request yoksa (stdio) env'deki FOOD_API_TOKEN'a düş."""
    try:
        req = mcp.get_context().request_context.request
    except (LookupError, AttributeError):
        req = None
    if req is not None:
        auth = req.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            tok = auth[7:].strip()
            if tok:
                return tok
    if API_TOKEN:
        return API_TOKEN
    raise RuntimeError(
        "Missing bearer token: send 'Authorization: Bearer <token>' header "
        "or set FOOD_API_TOKEN env."
    )


def _request(method: str, path: str, params: Optional[dict] = None,
             body: Optional[dict] = None) -> Any:
    """HTTP request gönder, JSON yanıt döndür."""
    url = f"{API_URL}{path}"
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url += "?" + urllib.parse.urlencode(clean, doseq=True)
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Authorization": f"Bearer {_resolve_token()}"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            if not raw:
                return None
            return json.loads(raw.decode())
    except urllib.error.HTTPError as e:
        msg = e.read().decode()[:300]
        try:
            j = json.loads(msg)
            msg = j.get("detail", msg)
        except Exception:
            pass
        raise RuntimeError(f"API HTTP {e.code}: {msg}")


# ===== Create =================================================================

@mcp.tool()
def log_food(
    food_name: str,
    weight_g: float,
    meal_type: str,
    calories: float = 0,
    protein_g: float = 0,
    carbs_g: float = 0,
    fat_g: float = 0,
    fiber_g: float = 0,
    sugar_g: float = 0,
    sodium_mg: float = 0,
    notes: Optional[str] = None,
    entry_date: Optional[str] = None,
    entry_time: Optional[str] = None,
) -> dict[str, Any]:
    """
    Bir yemek kaydı ekle.

    Args:
        food_name: ör. "ızgara tavuk göğsü"
        weight_g: yenen miktar (gram)
        meal_type: breakfast | lunch | dinner | snack
        calories, protein_g, carbs_g, fat_g, fiber_g, sugar_g, sodium_mg:
            yenen porsiyon için makro/mikro değerler (100g başına değil)
        notes: serbest metin
        entry_date: YYYY-MM-DD, varsayılan bugün
        entry_time: HH:MM, varsayılan şu an
    """
    return _request("POST", "/api/entries", body={
        "food_name": food_name, "weight_g": weight_g, "meal_type": meal_type,
        "calories": calories, "protein_g": protein_g, "carbs_g": carbs_g,
        "fat_g": fat_g, "fiber_g": fiber_g, "sugar_g": sugar_g,
        "sodium_mg": sodium_mg, "notes": notes,
        "entry_date": entry_date, "entry_time": entry_time,
    })


# ===== Read ===================================================================

@mcp.tool()
def list_entries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    meal_type: Optional[str] = None,
    food_query: Optional[str] = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    """
    Kayıtları filtreyle listele.

    Args:
        start_date / end_date: YYYY-MM-DD inclusive
        meal_type: tek meal type'a filtrele
        food_query: food_name içinde substring araması (case-insensitive)
        limit: max sonuç (en yenisinden başlayarak)
    """
    return _request("GET", "/api/entries", params={
        "start_date": start_date, "end_date": end_date,
        "meal_type": meal_type, "food_query": food_query, "limit": limit,
    })


@mcp.tool()
def get_recent_meals(n: int = 10) -> list[dict[str, Any]]:
    """En yeni n kaydı döndür (en yenisi başta)."""
    return _request("GET", "/api/entries", params={"limit": n})


# ===== Update / Delete ========================================================

@mcp.tool()
def update_entry(entry_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    """
    Mevcut bir kaydın alanlarını güncelle.

    Args:
        entry_id: UUID
        updates: column -> new value dict (sadece bilinen alanlar uygulanır)
    """
    return _request("PATCH", f"/api/entries/{entry_id}", body=updates)


@mcp.tool()
def delete_entry(entry_id: str) -> dict[str, Any]:
    """Kaydı UUID ile sil."""
    return _request("DELETE", f"/api/entries/{entry_id}")


# ===== Analytics ==============================================================

@mcp.tool()
def get_daily_totals(target_date: Optional[str] = None) -> dict[str, Any]:
    """Tek bir günün toplam makro+mikro değerlerini döndür. Default: bugün."""
    return _request("GET", "/api/analytics/daily", params={"target_date": target_date})


@mcp.tool()
def get_date_range_summary(start_date: str, end_date: str) -> dict[str, Any]:
    """
    Tarih aralığındaki günlük toplamlar + ortalamalar.

    Args:
        start_date: YYYY-MM-DD
        end_date:   YYYY-MM-DD
    """
    return _request("GET", "/api/analytics/range", params={
        "start_date": start_date, "end_date": end_date,
    })


@mcp.tool()
def analyze_macros(
    start_date: str,
    end_date: str,
    target_calories: Optional[float] = None,
    target_protein_g: Optional[float] = None,
) -> dict[str, Any]:
    """
    Tarih aralığındaki makro dağılımı + (opsiyonel) hedef adherence.

    4/4/9 kcal/g formülü ile her makronun kalori payını hesaplar.
    Hedef verilirse her gün için adherence yüzdelerini döndürür.
    """
    return _request("GET", "/api/analytics/macros", params={
        "start_date": start_date, "end_date": end_date,
        "target_calories": target_calories, "target_protein_g": target_protein_g,
    })


@mcp.tool()
def find_food(query: str, limit: int = 20) -> dict[str, Any]:
    """food_name'e göre geçmiş kayıtları substring ile ara."""
    return _request("GET", "/api/analytics/find", params={"q": query, "limit": limit})


@mcp.tool()
def suggest_next_meal(meal_type: str) -> dict[str, Any]:
    """
    Son 30 günde belirtilen meal type için en sık yenen yemekler.
    'X için ne yiyeyim?' sorularına cevap verirken kullan.
    """
    return _request("GET", "/api/analytics/suggest", params={"meal_type": meal_type})


# ==============================================================================

if __name__ == "__main__":
    if TRANSPORT == "http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run()
