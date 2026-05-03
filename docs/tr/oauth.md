# OAuth 2.0

MCP server'ın HTTP transport modunda OAuth 2.0 + PKCE desteği vardır. ChatGPT Custom Connector, Claude.ai Custom Connector gibi servislerin "kullanıcı şifresini görmeden" senin adına API'ye konuşabilmesini sağlar.

## Roller

| Rol | Bizde kim |
|---|---|
| **User** | Tarayıcıda email+şifresi giren kişi (SPA hesabı sahibi) |
| **Client** | ChatGPT / Claude.ai connector |
| **Authorization Server** | MCP server (`/authorize`, `/token`, vb. endpoint'ler) |
| **Resource Server** | FastAPI app (`/api/*`) — gerçek veri burada |

Mevcut deployment'ta auth server ve resource server aynı süreçte çalışıyor; teorik olarak ayrılabilir.

## Akış (Authorization Code + PKCE)

1. Kullanıcı connector'a MCP URL verir: `https://server/mcp`
2. Connector → `GET /.well-known/oauth-authorization-server` (RFC 8414 metadata keşfi)
3. Server cevap verir: `authorization_endpoint`, `token_endpoint`, `registration_endpoint` URL'leri
4. Connector → `POST /register` (Dynamic Client Registration, RFC 7591) → `client_id` + `client_secret` alır
5. Connector kullanıcıyı şuraya yönlendirir:
   ```
   /authorize?client_id=...&redirect_uri=...&response_type=code
            &code_challenge=<S256 hash>&code_challenge_method=S256
            &state=<random>
   ```
6. Server `/oauth/login`'e redirect eder, kullanıcı SPA hesabı email+şifresi girer
7. Server şifreyi `/api/auth/login` üzerinden doğrular, başarılıysa kısa ömürlü bir **authorization code** üretir
8. Server `redirect_uri`'ye `?code=xxx&state=xxx` ile geri yönlendirir
9. Connector → `POST /token` (kod + `code_verifier` + `client_secret`) → **access_token** alır
10. Connector her MCP isteğinde `Authorization: Bearer <access_token>` gönderir
11. Server `load_access_token` ile bearer'ı `/api/me` çağırarak doğrular

## Endpoint'ler

| Path | RFC | Ne yapar |
|---|---|---|
| `/.well-known/oauth-authorization-server` | 8414 | Auth server metadata (endpoint listesi) |
| `/.well-known/oauth-protected-resource` | 9728 | Resource server metadata (hangi auth server kullanılır) |
| `/register` | 7591 | Dynamic Client Registration |
| `/authorize` | 6749 | Authorization endpoint |
| `/oauth/login` | — | Custom kullanıcı login formu (bizim eklentimiz) |
| `/token` | 6749 | Code → access_token exchange |
| `/revoke` | 7009 | Token iptali |

`/.well-known/*` endpoint'leri **fiziksel dosya değil** — runtime'da JSON üreten Python handler'larıdır. Kayıt yeri: `mcp/server/auth/routes.py`.

## PKCE neden var

Authorization code'u client'a döndürürken redirect URI üzerinden gidiyor. Bu URL kullanıcının tarayıcı geçmişinde, ağ proxy'sinde, log'larda görünebilir. Eğer biri bu kodu çalıp `/token` endpoint'ine gönderirse, normalde access_token alabilirdi.

PKCE bunu engelliyor:

1. Connector başlangıçta rastgele `code_verifier` üretir, SHA-256 hash'ini `code_challenge` olarak `/authorize`'a gönderir
2. `/token` çağrısında orijinal `code_verifier`'ı yollar
3. Server `SHA256(verifier) == saved_challenge` kontrolü yapar

Saldırgan kodu çalsa bile `code_verifier`'ı bilemez — kod çalmaz.

`code_challenge_method=S256` zorunlu, plain'i kabul etmiyoruz.

## Access token nedir

Kasıtlı kısayol: **access_token = kullanıcının `api_token`'ı**. OAuth dansı, mevcut bearer token sistemi üzerine sarmalama. Yeni bir token universe yok.

Sonuç:
- OAuth-issued bearer ile doğrudan paste'lenmiş bearer aynı `load_access_token` doğrulamasından geçer
- SPA'da "Rotate" deyince OAuth-bağlı tüm client'lar da geçersizleşir
- Refresh token yok, expires_in null — token kalıcı, sadece rotate ile iptal edilir

## State storage

OAuth provider (`mcp_server/oauth.py`) bellekteki dict'lerde tutar:

| Saklanır mı? | Neden |
|---|---|
| `_clients` (kayıtlı connector'lar) | **In-memory, restart'ta kaybolur**. Gerçek üretimde DB tablosu olmalı. Şu an: connector restart sonrası re-register olur. |
| `_sessions` (login bekleyen oturumlar) | In-memory, 10dk TTL — bu kadarı yeterli |
| `_codes` (one-time auth kodları) | In-memory, 5dk TTL — saniyelik kullanılır |
| `_token_cache` (api_token doğrulama cache'i) | In-memory, 60sn TTL — performans optimizasyonu |

Token'lar ayrıca saklanmaz çünkü `api_token` zaten Postgres'te `users` tablosunda. Doğrulama her isteğin `/api/me` çağrısı + cache ile yapılır.

## Yaygın hatalar

**"invalid_client"** — client_id bilinmiyor. Server restart olduysa client'lar in-memory dict'ten silinmiştir; connector yeniden register olmalı (genelde otomatik).

**"invalid_grant"** — kod kullanıldı, süresi doldu, veya `code_verifier` eşleşmiyor.

**Authorization sayfası localhost'a redirect ediyor** — `MCP_PUBLIC_URL` env yanlış set edilmiş. Public URL (ngrok URL'i veya production domain) olmalı.

**ChatGPT/Claude.ai bağlanmıyor, hata vermiyor** — `.well-known` URL'lerinin dış dünyadan erişilebilir olduğunu kontrol et. HTTPS şart, HTTP kabul edilmiyor.

## Yapılacaklar (production için)

- `_clients` ve `_codes`'u DB'ye persist et (`oauth_clients`, `oauth_codes` tabloları)
- Refresh token desteği ekle
- Gerçek consent ekranı (login = onay yerine, "X uygulaması şu yetkilere erişmek istiyor")
- Scope sistemi (read-only, write, vs.)
- Rate limiting login endpoint'inde (brute-force koruması)
