# Production Deployment Guide

Bu repo'daki compose stack'i development içindir. Public'e açmadan önce aşağıdaki maddeleri gözden geçir. Her madde için **ne** yapılması gerektiği yazılı; **hangi araçla** sana ve bütçene kalmış.

## 1. HTTPS şart

MCP client connector'ları (ve genel olarak public OAuth flow'u) HTTPS olmadan handshake yapmaz. Container'ların önüne TLS terminator koy (managed cloud load balancer, reverse proxy container, ya da tunnel servisi). `MCP_PUBLIC_URL`'ı bu domain'e güncelle.

## 2. Secrets compose'dan çıksın

Mevcut hardcoded değerler (DB şifresi, `ALLOWED_ORIGINS`, `MCP_PUBLIC_URL`) production'a gitmemeli. Yerine env file (gitignore'lu), Docker secret, ya da bulut sağlayıcının secret manager'ı kullan.

## 3. Frontend'i CDN'e at

Mevcut `frontend` container'ı dev-grade Vite dev server. Production için: `npm run build` çıktısını static host'a (Cloudflare Pages, Vercel, S3+CDN, kendi nginx'in, vb.) yükle. `frontend` compose service'ini production stack'inden tamamen kaldır.

## 4. Veritabanı için managed servis düşün

Postgres'i compose ile self-host yapacaksan backup, replication, point-in-time recovery, OS patch sorumlulukları sende. Managed bir servis (cloud provider'ın Postgres ürünleri) bu işlerin çoğunu üzerinden alır. Self-host'ta kalacaksan en azından düzenli pg_dump + offsite kopyala.

## 5. Migration'ları deploy step'inde çalıştır

Repo Alembic ile geliyor (`migrations/` klasörü, `alembic.ini`). Compose'da api service'i app start'tan önce `alembic upgrade head` koşuyor — single-replica dev için yeterli. Production'da:

- Multi-replica deployment'a geçeceksen migration'ı **CI/CD pipeline'ında** ayrı bir step olarak çalıştır, app boot'tan önce. Her replica'nın aynı anda upgrade çalıştırması race condition yaratabilir (Alembic advisory lock kullanıyor ama %100 garanti değil).
- Migration başarısız olursa pipeline'ı dur, app'i yeni schema beklerek başlatma.
- Yeni migration: `uv run alembic revision --autogenerate -m "..."` model değişikliğinden sonra. PR'a giriyor, code review'a açık.

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
