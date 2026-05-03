# Open Food Ledger

> Diller: [English](README.md) · **Türkçe**
> Belgeler: [English](docs/en/) · [Türkçe](docs/tr/)

Kişisel kalori, makro ve gramaj günlüğü. Tarayıcıdan veya yapay zeka asistanından yemek kaydı tut, gün/hafta toplamlarını gör, hedeflerine olan ilerlemeyi izle.

## Bu ne işe yarar?

Yediklerini kayda almanın üç yolu var:

- **Tarayıcıdan** — basit bir SPA: hesap aç, yemek ekle, gününü gör
- **Yapay zekadan** — Claude veya ChatGPT'ye doğal dilde yaz: *"80g yulaf, kahvaltı, 320 kalori"* — yapay zeka kendisi kaydeder, sorgular, analiz eder
- **Excel'e aktararak** — kendi raporunu yap, başka uygulamalarla entegre et

Veri tamamen senin Postgres'inde, kontrol sende.

## Hızlı başlangıç

Tek gereken: Docker.

```bash
git clone <repo-url> open-food-ledger
cd open-food-ledger
docker compose -f compose.dev.yml up --build
```

Production benzeri stack için (frontend yok, source baked, no reload):
```bash
docker compose -f compose.prod.yml up --build -d
```

Dev stack'inde dört container kalkar:

| Container | Port | Ne yapar |
|---|---|---|
| `frontend` | http://localhost:5173 | Vite dev server (Node 20), HMR aktif, `/api/*`'ı `:8000`'e proxy'ler |
| `api` | http://localhost:8000 | FastAPI, sadece JSON (`/api/*`, `/docs`) |
| `db` | :5432 | PostgreSQL 16 |

Tarayıcıda **http://localhost:5173** adresini aç, **Create account** ile kayıt ol (şifre min. 8 karakter), yemek eklemeye başla. İlk açılışta Postgres bir-iki saniye init olur, tablolar otomatik yaratılır.

> **Not:** `frontend` container'ı dev-grade Vite dev server kullanır (HMR + source bind mount). `compose.prod.yml`'de frontend service'i **yok** — production deployment (static hosting, CDN, edge cache) CI/CD veya cloud provider tarafına bırakılır (Vercel, Cloudflare Pages, S3 + CloudFront, vb.).

## Yapay zekaya bağlamak

İki yol:

- **Claude Desktop / Claude Code** — yerel makinende, stdio transport ile
- **ChatGPT, Claude.ai connector** veya başka bir uzak client — HTTPS + OAuth ile

Her iki kurulumun adım adım anlatımı: **[docs/tr/mcp.md](docs/tr/mcp.md)** ([English](docs/en/mcp.md))

Örnek istemler bağlandıktan sonra:
> *"Bugün ne yedim, kaç kalori aldım?"*
> *"80g yulaf ezmesi, 320 kalori, 10g protein olarak kahvaltı ekle"*
> *"Son hafta makro dağılımım nasıl, 2200 kalori 140g protein hedefime adherence'ım ne?"*

## Daha fazla bilgi

| Belge | TR | EN |
|---|---|---|
| MCP server kurulumu (stdio ve HTTP), tool listesi, örnek konfigler | [tr/mcp.md](docs/tr/mcp.md) | [en/mcp.md](docs/en/mcp.md) |
| REST API endpoint referansı | [tr/api.md](docs/tr/api.md) | [en/api.md](docs/en/api.md) |
| OAuth 2.0 akışı, `.well-known` endpoint'leri, PKCE detayı | [tr/oauth.md](docs/tr/oauth.md) | [en/oauth.md](docs/en/oauth.md) |
| Mimari diyagramı, veri şeması, auth modeli, güvenlik notları | [tr/architecture.md](docs/tr/architecture.md) | [en/architecture.md](docs/en/architecture.md) |
| Production deployment guide — HTTPS, secrets, migrations, rate limiting, observability | [tr/deployment.md](docs/tr/deployment.md) | [en/deployment.md](docs/en/deployment.md) |

## Geliştirme

`docker compose up` her şeyi kaldırır, ama daha hızlı iterasyon için:

**Backend (Docker'sız):**
```bash
uv sync                                         # creates .venv, installs from uv.lock
export DATABASE_URL="postgresql+psycopg://openfoodledger:openfoodledger@localhost:5432/openfoodledger"
uv run uvicorn app.main:app --reload
```

`pyproject.toml` + `uv.lock` tek kaynak — `requirements.txt` yok. Yeni dependency için: `uv add <paket>`.

`compose.dev.yml`'de api service'i `target: dev` build target'ı ile çalışır (Dockerfile'da `--reload` baked) ve `./app` host'tan mount'lanır — Python kod değişiklikleri anında yansır. `compose.prod.yml` ise `target: prod` kullanır: source baked, bind mount yok, reload yok.

**Frontend (Vite hot-reload, Node 18+):**
```bash
cd frontend
npm install
npm run dev   # → http://localhost:5173, /api/* requests proxied to :8000
```

Frontend kod değiştiğinde container'ı yeniden build et: `docker compose up --build frontend`.

**Stack:** FastAPI + SQLAlchemy 2.0 + psycopg + bcrypt + openpyxl, PostgreSQL 16, React + Vite + TypeScript SPA (`frontend/`), `mcp>=1.27.0`. Detaylar [docs/tr/architecture.md](docs/tr/architecture.md).

## Lisans

MIT (veya kendi tercihin).
