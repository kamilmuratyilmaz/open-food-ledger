# Food Tracker

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
git clone <repo-url> food-tracker
cd food-tracker
docker compose up
```

Sonra http://localhost:8000 adresini aç, **Create account** ile kayıt ol (şifre min. 8 karakter), yemek eklemeye başla. İlk açılışta Postgres bir-iki saniye init olur, tablolar otomatik yaratılır.

## Yapay zekaya bağlamak

İki yol:

- **Claude Desktop / Claude Code** — yerel makinende, stdio transport ile
- **ChatGPT, Claude.ai connector** veya başka bir uzak client — HTTPS + OAuth ile

Her iki kurulumun adım adım anlatımı: **[docs/mcp.md](docs/mcp.md)**

Örnek istemler bağlandıktan sonra:
> *"Bugün ne yedim, kaç kalori aldım?"*
> *"80g yulaf ezmesi, 320 kalori, 10g protein olarak kahvaltı ekle"*
> *"Son hafta makro dağılımım nasıl, 2200 kalori 140g protein hedefime adherence'ım ne?"*

## Daha fazla bilgi

| Belge | İçerik |
|---|---|
| [docs/mcp.md](docs/mcp.md) | MCP server kurulumu (stdio ve HTTP), tool listesi, örnek konfigler |
| [docs/api.md](docs/api.md) | REST API endpoint referansı |
| [docs/oauth.md](docs/oauth.md) | OAuth 2.0 akışı, `.well-known` endpoint'leri, PKCE detayı |
| [docs/architecture.md](docs/architecture.md) | Mimari diyagramı, veri şeması, auth modeli, güvenlik notları |

## Geliştirme

Backend'i Docker olmadan çalıştır:

```bash
pip install -r requirements.txt
export DATABASE_URL="postgresql+psycopg://foodtracker:foodtracker@localhost:5432/foodtracker"
uvicorn app:app --reload
```

`docker-compose.yml` `--reload` ile çalışır, kod değişiklikleri anında yansır.

**Stack:** FastAPI + SQLAlchemy 2.0 + psycopg + bcrypt + openpyxl, PostgreSQL 16, Vanilla SPA, `mcp>=1.27.0`. Detaylar [docs/architecture.md](docs/architecture.md).

## Lisans

MIT (veya kendi tercihin).
