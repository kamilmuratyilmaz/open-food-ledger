# Production Deployment Guide

Bu repo'daki compose stack'i development içindir. Public'e açmadan önce aşağıdaki maddeleri gözden geçir. Her madde için **ne** yapılması gerektiği yazılı; **hangi araçla** sana ve bütçene kalmış.

## 1. HTTPS şart

MCP client connector'ları (ve genel olarak public OAuth flow'u) HTTPS olmadan handshake yapmaz. Container'ların önüne TLS terminator koy (managed cloud load balancer, reverse proxy container, ya da tunnel servisi). `MCP_PUBLIC_URL`'ı bu domain'e güncelle.

## 2. Secrets compose'dan çıksın

`compose.prod.yml` artık `.env.prod` dosyasından okuyor (`env_file:` direktifi). İlk deploy'dan önce:

```bash
cp .env.prod.example .env.prod
# .env.prod'u editle: gerçek POSTGRES_PASSWORD, DATABASE_URL, ALLOWED_ORIGINS, MCP_PUBLIC_URL
```

`.env.prod` `.gitignore`'da (commit'e gitmez), `.env.prod.example` template repo'da. Daha hardcore: bulut sağlayıcının secret manager'ından (AWS Secrets Manager, Vault, vb.) deploy time'da inject et — `.env.prod` dosyası diskte hiç durmasın.

## 3. Frontend'i CDN'e at

Mevcut `frontend` container'ı dev-grade Vite dev server. Production için: `npm run build` çıktısını static host'a (Cloudflare Pages, Vercel, S3+CDN, kendi nginx'in, vb.) yükle. `frontend` compose service'ini production stack'inden tamamen kaldır.

## 4. Veritabanı için managed servis düşün

Postgres'i compose ile self-host yapacaksan backup, replication, point-in-time recovery, OS patch sorumlulukları sende. Managed bir servis (cloud provider'ın Postgres ürünleri) bu işlerin çoğunu üzerinden alır. Self-host'ta kalacaksan en azından düzenli pg_dump + offsite kopyala.

## 5. Migration'ları deploy step'inde çalıştır

Repo Alembic ile geliyor (`migrations/` klasörü, `alembic.ini`). Tek replica'lı dev/prod stack'inde api container'ı boot olurken `alembic upgrade head` zaten koşar — sorun yok.

**Multi-replica'ya geçtiğinde** (yük dengeleyici arkasında 2+ api kopyası): hepsi aynı anda upgrade'e kalkışırsa race condition yaratabilir. Alembic Postgres advisory lock kullanır ama %100 garantili değil. O yüzden migration **container boot'undan ayrı**, deploy adımı olarak koşmalı.

Repo'da hazır script var:

```bash
./scripts/migrate.sh
```

Bu script tek seferlik bir container açar (api image'ından, ama uvicorn yerine `alembic upgrade head`), DB'ye karşı koşar, biter, kendini temizler. Idempotent — pending migration yoksa no-op.

**CI/CD pipeline akışı:**
1. Yeni image'ı build et + registry'e push et
2. `./scripts/migrate.sh` (DATABASE_URL prod DB'yi gösteriyor olmalı)
3. Adım 2 başarısızsa pipeline'ı dur — app'i yeni schema beklerek başlatma, kullanıcı 500'lere düşer
4. Adım 2 başarılıysa api container'larını rolling-update et (artık migration zaten yapılmış, container'ların sadece uvicorn koşması yeter)

Multi-replica'ya geçince: prod compose'daki api `command:`'ından `alembic upgrade head &&` kısmını çıkar, sadece uvicorn bıraksın — script zaten halletmiş olacak.

**Yeni migration eklemek (dev workflow):**
```bash
# 1. Modeli değiştir (örn. app/db/models.py'a yeni kolon ekle)
# 2. Migration üret
uv run alembic revision --autogenerate -m "add display_name to users"
# 3. migrations/versions/xxx_add_display_name_to_users.py git'e gir, PR'a koy
# 4. Reviewer migration file'ını da diff'te görür ve inceler
```

## 6. Rate limiting ekle

`/api/auth/login`, `/api/auth/register`, `/oauth/login` brute force'a açık. FastAPI için bir rate-limit middleware'i ekle ve özellikle bu endpoint'lere düşük limit (örn. dakikada 5 istek) koy.

## 7. CORS'u daralt

`ALLOWED_ORIGINS=*` → gerçek frontend domain'in. Birden fazla varsa virgülle ayır.

## 8. Hata takibi

En azından bir error tracker (cloud-managed bir hizmet) ekle; uygulama hataları sessizce gömülmez. Structured (JSON) log formatına geçmek log toplama servisleriyle entegrasyonu kolaylaştırır.

## 9. Network'ü kıs

Compose'daki port mappings'lerini gözden geçir: sadece TLS terminator public expose edilsin. `api` (:8000), `mcp` (:8001), `db` (:5432) internal kalmalı — container'lar arası haberleşme compose internal DNS üzerinden zaten çalışıyor.

## 10. Container hijyeni

- Image tag'leri pin'le (`latest` kullanma)
- Image scanning'i CI'a bağla
- `restart: unless-stopped`, resource limit (memory/cpu), log driver size limit
- Image registry'sine yükle, build'i deploy ile ayır

## 11. Privacy / TOS

Yemek günlüğü potansiyel sağlık verisi. SPA'ya privacy policy + TOS sayfası ekle, user'a "delete my account" butonu ver (cascade delete zaten mevcut, endpoint eklemen yeter), data export zaten var (`GET /api/export/xlsx`). Yargı bölgene göre KVKK/GDPR yükümlülüklerini kontrol et.

## 12. OAuth state'i

`mcp_server/oauth.py`'da `_clients` ve `_codes` in-memory. Tek replica çalışıyorsan kabul edilebilir (restart'ta client'lar re-register olur, kullanıcı bir login akışı daha görür). Multi-replica deployment'a geçeceksen state'i ortak bir store'a (Postgres tablosu veya in-memory cache servisi) taşı.

---

## Minimum sıra

Eğer önce neyi yapayım dersen: **HTTPS → secrets dışı → migration tool → rate limit → error tracker.** Bu beşliyle küçük bir prod kurulumun standart riskleri kapanmış olur. Diğerleri trafik / kullanıcı sayısı arttıkça gelir.
