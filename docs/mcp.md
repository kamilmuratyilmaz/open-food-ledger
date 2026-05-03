# MCP Server

Yapay zeka asistanlarının yemek günlüğüne yazıp okuyabilmesi için MCP server'ı sunulur. İki transport modu destekler:

- **stdio** — yerel client'lar (Claude Desktop, Claude Code) subprocess olarak başlatır
- **streamable HTTP** — uzak client'lar (ChatGPT, Claude.ai connector) HTTP üzerinden bağlanır

## Tools

| Tool | Ne yapar |
|---|---|
| `log_food` | Yemek kaydı ekle (food_name, weight_g, meal_type, makrolar) |
| `list_entries` | Kayıtları filtreyle listele (tarih, öğün, isim arama) |
| `get_recent_meals` | Son N kaydı getir |
| `update_entry` | Var olan kaydı düzelt |
| `delete_entry` | Kaydı sil |
| `get_daily_totals` | Günün toplam makro+mikro değerleri (öğün kırılımıyla) |
| `get_date_range_summary` | Tarih aralığı özeti + günlük ortalamalar |
| `analyze_macros` | Makro dağılımı (4/4/9 kcal/g) + hedef adherence yüzdeleri |
| `find_food` | Geçmiş kayıtlarda yemek adı substring araması |
| `suggest_next_meal` | Son 30 günde belirtilen meal type için en sık yenenler |

## A) Yerel kurulum (stdio)

**Claude Desktop / Claude Code** lokal makinende çalışır. MCP server bir Python subprocess olarak başlatılır, stdin/stdout üzerinden JSON-RPC ile konuşulur.

### Kurulum

1. Python ortamına `mcp` paketini kur:
   ```bash
   pip install mcp
   ```

2. SPA'da hesap aç, **Settings → MCP token** bölümünden **Reveal → Copy** ile token'ını al.

3. Config dosyana ekle:

   **Claude Code (proje scope):** proje kökünde `.mcp.json`
   **Claude Desktop:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows) / `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac)

   ```json
   {
     "mcpServers": {
       "food-tracker": {
         "command": "/absolute/path/to/python",
         "args": ["-m", "mcp_server.server"],
         "cwd": "/absolute/path/to/food-tracker",
         "env": {
           "FOOD_API_URL": "http://localhost:8000",
           "FOOD_API_TOKEN": "<SPA'dan kopyaladığın token>"
         }
       }
     }
   }
   ```

   `cwd` field'ı `python -m mcp_server.server`'ın `mcp_server` paketini bulması için gerekli. Client'ın `cwd` field'ını desteklemiyorsa direkt path versiyonu da çalışır (server.py'da sys.path injection var):
   ```json
   "args": ["/absolute/path/to/food-tracker/mcp_server/server.py"]
   ```

4. Client'ı yeniden başlat. Tool'lar listede görünecek.

### Akış

Client → MCP server'ı subprocess olarak başlatır → server `FOOD_API_TOKEN` env'i ile FastAPI'ya bearer auth ile bağlanır → tool'lar JSON-RPC üzerinden çağrılır.

Tek kullanıcılı bir kurulum: env'deki token kimin token'ıysa o hesabın günlüğüne yazılır.

## B) Uzak kurulum (HTTP + OAuth)

**ChatGPT Custom Connector** veya **Claude.ai Custom Connector** gibi uzak servisler subprocess başlatamaz, HTTP üzerinden bağlanır. Bu modda OAuth 2.0 ile her kullanıcı kendi hesabıyla bağlanır.

### Server'ı başlat

```bash
export MCP_TRANSPORT=http
export MCP_PORT=8001                              # opsiyonel, default 8001
export MCP_PUBLIC_URL=https://your-domain.example  # gerekli, OAuth metadata için
export FOOD_API_URL=http://localhost:8000          # API'nin nerede çalıştığı
python -m mcp_server.server                        # proje kökünden
```

Endpoint: `https://your-domain.example/mcp`

### Connector'da kullan

1. Connector dialog'unda URL alanına `https://your-domain.example/mcp` yaz
2. OAuth Client ID/Secret alanlarını **boş bırak** (Dynamic Client Registration aktif, connector kendisi alır)
3. Bağlan'a bas
4. Browser açılır → **SPA hesabınla giriş yap** → kod üretilir → connector'a geri dönülür
5. Tool'lar görünmeli

### Yerelden test (ngrok)

Yerel makinende test ediyorsan public bir HTTPS URL'ine ihtiyacın var (Claude.ai/ChatGPT bulutları localhost'a erişemez):

```bash
ngrok http 8001
# çıkan https URL'i MCP_PUBLIC_URL'e koy ve server'ı yeniden başlat
```

### MCP Inspector ile manuel test

Browser tabanlı bir araçla tool'ları manuel test etmek için:

```bash
npx @modelcontextprotocol/inspector
```

URL alanına `http://localhost:8001/mcp` yaz, `Authorization: Bearer <api_token>` header'ı ekle. OAuth handshake olmadan doğrudan bearer ile bağlanır.

## Auth modu seçimi

MCP server'ın bearer doğrulaması:

- **stdio:** `FOOD_API_TOKEN` env'inden okur, tek kullanıcılı
- **HTTP + OAuth:** her isteğin `Authorization: Bearer` header'ından okur, çok kullanıcılı
- **HTTP + bearer doğrudan:** OAuth aktif olmasına rağmen client direkt bearer gönderebilir, geçerliliği `/api/me` ile doğrulanır (Inspector, ChatGPT bearer mode, vs.)

OAuth detayı: [oauth.md](oauth.md)

## Yaygın hatalar

**"FOOD_API_TOKEN env değişkenini ayarla"** — stdio modunda env'de token yok. Config'in `env` bloğunu kontrol et.

**"406 Not Acceptable"** — HTTP endpoint'ine `text/event-stream` accept header'ı olmadan GET geldi. Normal davranış, gerçek MCP client'lar doğru header'ı gönderir.

**"Invalid token"** — bearer geçersiz veya rotate edilmiş. SPA'dan yeni token al.

**Browser login sayfası açılmıyor (uzak modda)** — `MCP_PUBLIC_URL` set edilmemiş veya yanlış. Connector localhost'a redirect ediyor olabilir, log'lara bak.
