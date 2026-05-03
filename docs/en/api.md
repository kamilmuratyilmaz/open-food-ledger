# API Reference

Base URL: `http://localhost:8000` (Docker) or your own deployment.

Every endpoint except auth requires `Authorization: Bearer <api_token>`. You get the token from the response of `/api/auth/register` or `/api/auth/login`, and you can also see it in the SPA's Settings panel.

## Auth

### `POST /api/auth/register`
Creates a new account and returns a token.

```json
// Body
{ "email": "user@example.com", "password": "min8chars" }

// Response 200
{ "user_id": "uuid", "email": "user@example.com", "api_token": "..." }
```

### `POST /api/auth/login`
Existing account; returns the **same** token (idempotent — does not mint a new one).

```json
{ "email": "user@example.com", "password": "..." }
```

### `GET /api/me`
Current user info.

```json
{ "user_id": "uuid", "email": "...", "api_token": "...", "created_at": "..." }
```

### `POST /api/me/rotate-token`
Generates a new token and invalidates the old one. All active clients (SPA, MCP, OAuth) must re-authenticate.

## Entries

### `POST /api/entries`
New food entry.

```json
{
  "food_name": "grilled chicken breast",
  "weight_g": 150,
  "meal_type": "lunch",
  "calories": 247, "protein_g": 46, "carbs_g": 0, "fat_g": 5,
  "fiber_g": 0, "sugar_g": 0, "sodium_mg": 75,
  "notes": "peppered",
  "entry_date": "2026-05-03",   // optional, defaults to today
  "entry_time": "13:00"         // optional, defaults to now
}
```

`meal_type`: `breakfast` | `lunch` | `dinner` | `snack`

### `GET /api/entries`
Filtered list (newest first).

Query params:
- `start_date`, `end_date` — `YYYY-MM-DD` (inclusive)
- `meal_type` — filter to a single meal
- `food_query` — substring search on `food_name` (case-insensitive)
- `limit` — max results (default 200)

### `PATCH /api/entries/{id}`
Partial update. Body contains only the fields you want to change.

### `DELETE /api/entries/{id}`
Deletes the entry. Returns 204.

## Analytics

### `GET /api/analytics/daily?target_date=YYYY-MM-DD`
Total macro+micro values for a single day, broken down by meal. Defaults to today if `target_date` is omitted.

### `GET /api/analytics/range?start_date=&end_date=`
Date range: per-day totals + averages.

### `GET /api/analytics/macros?start_date=&end_date=&target_calories=&target_protein_g=`
Macro distribution (4/4/9 kcal/g). When `target_*` are provided, also returns daily adherence percentages.

### `GET /api/analytics/find?q=&limit=`
Substring search on `food_name`.

### `GET /api/analytics/suggest?meal_type=`
Most frequently eaten foods for the given `meal_type` over the last 30 days.

## Export

### `GET /api/export/xlsx?start_date=&end_date=`
Downloads the dump as an XLSX file. Importable into Google Sheets.

## Error responses

Errors follow the standard FastAPI/Pydantic shape:

```json
{ "detail": "..." }
```

Common codes:
- `400` — input validation
- `401` — missing/invalid bearer
- `404` — resource not found (e.g., unknown entry_id)
- `422` — Pydantic schema validation
