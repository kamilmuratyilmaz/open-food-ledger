# Architecture

## Bileşenler

```
┌──────────┐   ┌────────────┐   ┌────────────┐
│   SPA    │   │   Claude   │   │  ChatGPT   │
│ (browser)│   │  Desktop   │   │  Connector │
└─────┬────┘   └─────┬──────┘   └─────┬──────┘
      │              │                │
      │  bearer      │  stdio         │  OAuth + bearer
      │  (paste)     │  (subprocess)  │  (HTTPS)
      └─────┬────────┴────────────────┘
            │
   ┌────────▼─────────┐  ◀ port 8000
   │    FastAPI       │
   │   /api/auth/*    │
   │   /api/entries/* │
   │   /api/analytics/*│
   │   /api/export/*  │
   │   StaticFiles    │  ← SPA /
   └────────┬─────────┘
            │
   ┌────────▼─────────┐  ◀ port 8001 (HTTP modunda)
   │   MCP Server     │
   │   /mcp           │  ← streamable HTTP transport
   │   /authorize     │
   │   /token         │
   │   /oauth/login   │
   │   /.well-known/* │
   └────────┬─────────┘
            │
   ┌────────▼─────────┐
   │   PostgreSQL 16  │
   │   users          │
   │   food_entries   │
   └──────────────────┘
```

`docker-compose.yml` SPA + API + DB'yi ayağa kaldırır. MCP server şu an Docker dışında çalışıyor (host'ta veya ayrı container'da). Tek deployment'a birleştirmek için `app.py`'a MCP'yi mount etmek gerekir — şu an ayrı tutuldu.

## Auth modeli

Kasıtlı olarak basit:

- Her kullanıcı kayıt olunca **tek** bir `api_token` alır (`secrets.token_urlsafe(32)`)
- Token DB'de `users.api_token` sütununda, unique index'li
- SPA token'ı `localStorage`'da, MCP server `env`'de veya request header'ında, OAuth client'ları access_token olarak tutar — **hepsi aynı token**
- Token rotation: `POST /api/me/rotate-token` → tüm aktif kanallar geçersizleşir
- JWT yok, refresh token yok, oturum yönetimi yok

**Avantaj:** zihinsel yük düşük, debugging kolay. **Dezavantaj:** scope yok (her token full access), expiration yok (rotate olmadan kalıcı).

## Veri şeması

```sql
users:
  id              uuid PRIMARY KEY
  email           text UNIQUE NOT NULL
  password_hash   text NOT NULL                   -- bcrypt
  api_token       text UNIQUE NOT NULL            -- secrets.token_urlsafe(32)
  created_at      timestamptz DEFAULT now()

food_entries:
  id          uuid PRIMARY KEY
  user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE
  entry_date  date NOT NULL
  entry_time  text NOT NULL                       -- 'HH:MM'
  meal_type   text NOT NULL                       -- breakfast|lunch|dinner|snack
  food_name   text NOT NULL
  weight_g    numeric NOT NULL
  calories    numeric DEFAULT 0
  protein_g   numeric DEFAULT 0
  carbs_g     numeric DEFAULT 0
  fat_g       numeric DEFAULT 0
  fiber_g     numeric DEFAULT 0
  sugar_g     numeric DEFAULT 0
  sodium_mg   numeric DEFAULT 0
  notes       text
  created_at  timestamptz DEFAULT now()
```

Tablolar uygulama boot'ta `Base.metadata.create_all(engine)` ile oluşturulur — migration aracı yok. Şema değişikliği için elle migration veya schema reset gerekir.

## Stack detayı

- **FastAPI 0.115+** — REST API
- **SQLAlchemy 2.0** (sync) — ORM
- **psycopg 3** — Postgres driver
- **bcrypt 4.2+** — şifre hash'leme
- **openpyxl 3.1+** — XLSX export
- **pydantic 2** — request/response validation
- **PostgreSQL 16** — DB
- **mcp 1.27+** — MCP protocol implementation, FastMCP ile

Frontend: vanilla HTML/CSS/JS (build step yok), `static/index.html` tek dosya.

## Güvenlik

- **Şifreler** bcrypt ile hash'lenir, plain'de saklanmaz
- **API token'lar** `secrets.token_urlsafe(32)` ile üretilir (256 bit entropy)
- **OAuth flow** PKCE S256 zorunlu kılar (plain method reddedilir)
- **DB cascade delete** — kullanıcı silinince kayıtları da silinir
- **CORS** SPA aynı origin'den serve edildiği için sorun değil; başka origin'den çağrılırsa `app.py`'da `CORSMiddleware` eklemek gerekir
- **Rate limiting yok** — public deployment'a koymadan önce login ve register endpoint'lerine eklemen önerilir
- **Email doğrulama yok** — production'da SMTP entegrasyonu eklemelisin

## Deployment notları

Public deployment için minimum:

- HTTPS (Caddy / Nginx / cloud LB)
- `MCP_PUBLIC_URL` env'i public domain'e set edilmeli (OAuth metadata için)
- Postgres volume backup stratejisi
- `POSTGRES_PASSWORD` ortam değişkenine alın, hardcode etmeyin
- Container'lar arasında network izolasyonu

OAuth state'ini ölçekleyebilmek için (multi-replica deployment): `oauth.py`'daki in-memory dict'leri Redis veya Postgres'e taşı.
