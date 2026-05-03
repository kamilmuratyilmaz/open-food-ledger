# API Reference

Base URL: `http://localhost:8000` (Docker) veya kendi deployment'ın.

Auth endpoint'leri hariç tüm endpoint'ler `Authorization: Bearer <api_token>` ister. Token'ı `/api/auth/register` veya `/api/auth/login` dönüşünden alırsın, SPA'da Settings'ten görebilirsin.

## Auth

### `POST /api/auth/register`
Yeni hesap oluşturur, token döner.

```json
// Body
{ "email": "user@example.com", "password": "min8chars" }

// Response 200
{ "user_id": "uuid", "email": "user@example.com", "api_token": "..." }
```

### `POST /api/auth/login`
Mevcut hesap, **aynı** token'ı döner (idempotent — yeni token üretmez).

```json
{ "email": "user@example.com", "password": "..." }
```

### `GET /api/me`
Kullanıcı bilgisi.

```json
{ "user_id": "uuid", "email": "...", "api_token": "...", "created_at": "..." }
```

### `POST /api/me/rotate-token`
Yeni token üretir, eskisi geçersizleşir. Tüm aktif client'lar (SPA, MCP, OAuth) yeniden auth almak zorunda kalır.

## Entries

### `POST /api/entries`
Yeni yemek kaydı.

```json
{
  "food_name": "ızgara tavuk göğsü",
  "weight_g": 150,
  "meal_type": "lunch",
  "calories": 247, "protein_g": 46, "carbs_g": 0, "fat_g": 5,
  "fiber_g": 0, "sugar_g": 0, "sodium_mg": 75,
  "notes": "biberli",
  "entry_date": "2026-05-03",   // opsiyonel, default bugün
  "entry_time": "13:00"         // opsiyonel, default şu an
}
```

`meal_type`: `breakfast` | `lunch` | `dinner` | `snack`

### `GET /api/entries`
Filtreli liste (en yeniden eskiye).

Query params:
- `start_date`, `end_date` — `YYYY-MM-DD` (inclusive)
- `meal_type` — tek öğüne filtrele
- `food_query` — `food_name` substring araması (case-insensitive)
- `limit` — max sonuç (default 200)

### `PATCH /api/entries/{id}`
Partial update. Body sadece değiştirilecek alanları içerir.

### `DELETE /api/entries/{id}`
Kaydı sil. 204 döner.

## Analytics

### `GET /api/analytics/daily?target_date=YYYY-MM-DD`
Tek bir günün toplam makro+mikro değerleri, öğün kırılımıyla. `target_date` boşsa bugün.

### `GET /api/analytics/range?start_date=&end_date=`
Tarih aralığı: günlük toplamlar listesi + ortalama.

### `GET /api/analytics/macros?start_date=&end_date=&target_calories=&target_protein_g=`
Makro dağılımı (4/4/9 kcal/g). `target_*` verilirse her gün için adherence yüzdesi döner.

### `GET /api/analytics/find?q=&limit=`
`food_name` substring araması.

### `GET /api/analytics/suggest?meal_type=`
Son 30 günde belirtilen `meal_type` için en sık yenenler.

## Export

### `GET /api/export/xlsx?start_date=&end_date=`
XLSX dosyası olarak dökümü indirir. Google Sheets'e import edilebilir.

## Hata yanıtları

Hatalar standart FastAPI/Pydantic formatında döner:

```json
{ "detail": "..." }
```

Yaygın kodlar:
- `400` — input validation
- `401` — bearer eksik/geçersiz
- `404` — kaynak yok (ör. var olmayan entry_id)
- `422` — pydantic schema validation
