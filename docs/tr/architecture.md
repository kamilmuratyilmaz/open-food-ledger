# Architecture

## Bileşenler

```
                  Browser                   Claude Desktop      ChatGPT
                     │                           │                 │
                     │ http                      │ stdio           │ OAuth + bearer
                     ▼                           │                 │
   ┌─────────────────────────────┐ ◀ :5173       │                 │
   │  frontend  (Vite dev)       │               │                 │
   │  ─ React SPA + HMR          │               │                 │
   │  ─ /api/* proxy → api:8000  │  (vite.config) │                 │
   └─────────────┬───────────────┘               │                 │
                 │                               │                 │
                 ▼                               ▼                 ▼
   ┌─────────────────────────────┐ ◀ :8000   ┌──────────────────────────┐ ◀ :8001
   │  api  (FastAPI)             │           │  mcp  (FastMCP container)│
   │  /api/auth/*                │           │  /mcp                    │
   │  /api/entries/*             │           │  /authorize, /token      │
   │  /api/analytics/*           │           │  /oauth/login            │
   │  /api/export/*              │           │  /.well-known/*          │
   │  /docs                      │           └────────────┬─────────────┘
   └─────────────┬───────────────┘                        │
                 │                            FOOD_API_URL=http://api:8000
                 │                                        │
                 └──────────────┬─────────────────────────┘
                                ▼
                  ┌─────────────────────────────┐ ◀ :5432
                  │  db  (PostgreSQL 16)        │
                  │  users, food_entries        │
                  └─────────────────────────────┘
```

İki compose dosyası var:

- **`compose.dev.yml`** — dört container kaldırır: **frontend** (Vite dev server, HMR), **api** (FastAPI `target: dev`, `--reload`, source bind mount), **mcp** (FastMCP HTTP + OAuth, source bind mount), **db** (Postgres). `docker compose -f compose.dev.yml up --build`.
- **`compose.prod.yml`** — üç container: **api** (`target: prod`, source baked, no reload, no bind mount), **mcp** (image-baked source), **db**. Frontend YOK — production'da CI/CD ile static build → CDN/static host. `docker compose -f compose.prod.yml up --build -d`.

`Dockerfile`'in multi-stage yapısı dev/prod farkını sağlıyor (`base` → `dev` → `prod` stage'leri, `dev` ve `prod` aynı katmanlardan türeyip sadece CMD'de farklılaşıyor — biri `--reload` ekler, diğeri eklemez). MCP container'ı compose internal DNS üzerinden API'ye bağlanıyor (`FOOD_API_URL=http://api:8000`); `MCP_PUBLIC_URL` browser'a görünen URL (local'de `http://localhost:8001`, production'da public domain).

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

Tablolar Alembic ile yönetiliyor (`migrations/` klasörü, `alembic.ini`). Compose'da api service'i app start'tan önce `alembic upgrade head` koşuyor — application code'da hiçbir `create_all` veya lifespan hook'u yok. Schema değişikliği: model'i güncelle, `uv run alembic revision --autogenerate -m "..."`, PR'a giren migration file'ı code review'dan geçiyor.

## Stack detayı

- **FastAPI 0.115+** — REST API
- **SQLAlchemy 2.0** (sync) — ORM
- **psycopg 3** — Postgres driver
- **bcrypt 4.2+** — şifre hash'leme
- **openpyxl 3.1+** — XLSX export
- **pydantic 2** — request/response validation
- **PostgreSQL 16** — DB
- **mcp 1.27+** — MCP protocol implementation, FastMCP ile

Frontend: React 18 + Vite 5 + TypeScript, kaynak `frontend/src/` içinde feature klasörlerinde organize:

- `frontend/src/features/{auth,entries,analytics,settings}/` — domain bazlı component'lar
- `frontend/src/components/` — cross-feature UI (Masthead, ToastHost)
- `frontend/src/context/AuthContext.tsx` — token + user state, login/register/signOut/rotateToken
- `frontend/src/hooks/{useEntries,useToast}.ts` — data fetching + global toast queue
- `frontend/src/lib/{api,storage,format}.ts` — fetch client (Bearer + 401 handling), localStorage, formatting
- `frontend/src/types/api.ts` — Pydantic schemas'a paralel TypeScript tipleri

State yönetimi minimal: AuthContext (cross-cutting) + useState (UI state) + custom hooks (server state). Redux/Zustand/TanStack Query yok. Navigation modal-based (auth screen ↔ app shell, settings slide-out) — react-router yok.

Vite production build (`cd frontend && npm run build`) `frontend/dist/` dizinine yazar. **frontend container** (multi-stage Dockerfile: Node 20 builder + nginx alpine) bu dist'i image'e bake eder ve `:80`'den serve eder. CSS tek bir global `frontend/src/styles.css` (paper/ink palette, Fraunces + DM Sans + JetBrains Mono).

nginx config (`frontend/nginx.conf`) iki şey yapar:
- `/api/*` → `http://api:8000` (Docker compose internal DNS, "api" service hostname)
- Diğer her şey → SPA fallback (`/index.html`), client-side routing eklenirse hazır

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

OAuth state'ini ölçekleyebilmek için (multi-replica deployment): `mcp_server/oauth.py`'daki in-memory dict'leri Redis veya Postgres'e taşı.
