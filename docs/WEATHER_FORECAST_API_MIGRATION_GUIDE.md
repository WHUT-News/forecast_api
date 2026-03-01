# Weather Forecast API - Migration Guide

This document outlines the breaking changes introduced by the Supabase migration. API clients must update their integrations accordingly.

## Overview

The backend storage has moved from Google CloudSQL to Supabase. Audio and image files are now served from Supabase Storage via public URLs instead of inline data.

---

## Breaking Changes

### 1. `GET /weather/{city}` - Forecast Response

#### Renamed Fields

| Old Field | New Field | Notes |
|---|---|---|
| `forecast.text` | `forecast.content` | Forecast text body |
| `forecast.picture_url` | `forecast.image_url` | Renamed for consistency |

#### Removed Fields

| Field | Replacement |
|---|---|
| `forecast.audio_base64` | Use `forecast.audio_url` instead (see below) |

#### New Fields

| Field | Type | Description |
|---|---|---|
| `forecast.audio_url` | `string \| null` | Public URL to audio file in Supabase Storage |
| `forecast.audio_format` | `string \| null` | Audio MIME type (e.g. `audio/mpeg`) |
| `forecast.audio_size_bytes` | `int \| null` | Audio file size |
| `forecast.image_url` | `string \| null` | Public URL to forecast image |
| `forecast.image_format` | `string \| null` | Image MIME type |
| `forecast.image_size_bytes` | `int \| null` | Image file size |
| `forecast.is_expired` | `bool` | Whether the forecast has expired |
| `forecast.age_seconds` | `int` | Seconds since forecast was created |
| `forecast.record_metadata` | `object` | Raw database record metadata |

#### New Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `language` | `string` | `null` | Filter by ISO 639-1 language code |
| `include_expired` | `bool` | `false` | Include expired forecasts in results |

#### Example Response (New)

```json
{
  "status": "success",
  "city": "chicago",
  "forecast": {
    "id": "abc-123",
    "city": "chicago",
    "content": "Today's weather in Chicago...",
    "forecast_at": "2025-01-27T10:00:00Z",
    "created_at": "2025-01-27T10:00:00Z",
    "expires_at": "2025-01-27T16:00:00Z",
    "is_expired": false,
    "age_seconds": 3600,
    "audio_url": "https://xxx.supabase.co/storage/v1/object/public/weather-audio/...",
    "audio_format": "audio/mpeg",
    "audio_size_bytes": 245760,
    "image_url": "https://xxx.supabase.co/storage/v1/object/public/weather-images/...",
    "image_format": "image/png",
    "image_size_bytes": 102400,
    "metadata": {
      "encoding": "utf-8",
      "language": "en",
      "locale": "en-US",
      "sizes": {
        "text": 1024,
        "audio": 245760,
        "image": 102400
      }
    },
    "record_metadata": {}
  }
}
```

---

### 2. `GET /weather/{city}/history` - History Response

#### New Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `language` | `string` | `null` | Filter by language code |
| `offset` | `int` | `0` | Pagination offset |
| `include_expired` | `bool` | `false` | Include expired forecasts |

#### Changed Fields in Each Forecast Summary

| Old Field | New Field |
|---|---|
| `language` | `text_language` |
| `expired` | `is_expired` |

#### New Fields in Each Forecast Summary

| Field | Type | Description |
|---|---|---|
| `has_audio` | `bool` | Whether the forecast has an audio file |
| `has_image` | `bool` | Whether the forecast has an image file |
| `text_size_bytes` | `int \| null` | Size of forecast text in bytes |

#### Example Response (New)

```json
{
  "status": "success",
  "city": "chicago",
  "count": 2,
  "forecasts": [
    {
      "id": "abc-123",
      "city": "chicago",
      "forecast_at": "2025-01-27T10:00:00Z",
      "created_at": "2025-01-27T10:00:00Z",
      "expires_at": "2025-01-27T16:00:00Z",
      "is_expired": false,
      "text_language": "en",
      "text_size_bytes": 1024,
      "has_audio": true,
      "has_image": true
    }
  ]
}
```

---

### 3. `GET /health` - Health Response

#### Changed Fields in `database` Object

| Old Field | New Field | Notes |
|---|---|---|
| `database.instance` | `database.supabase_url` | Now shows Supabase project URL |

#### New Fields in `database` Object

| Field | Type | Description |
|---|---|---|
| `database.table_exists` | `bool \| null` | Whether the `weather_forecasts` table exists |
| `database.record_count` | `int \| null` | Total rows in the table |

#### Removed Fields

| Field | Notes |
|---|---|
| `database.instance` | Replaced by `supabase_url` |

---

### 4. `GET /stats` - Statistics Response

#### Renamed Fields

| Old Field | New Field |
|---|---|
| `statistics.encodings_used` | Removed |

#### New Fields

| Field | Type | Description |
|---|---|---|
| `statistics.total_image_bytes` | `int` | Total image storage in bytes |
| `statistics.forecasts_with_images` | `int` | Count of forecasts with images |
| `statistics.cities_used` | `object` | Map of city name to forecast count |
| `statistics.languages_used` | `object` | Map of language code to forecast count |

---

## Audio Handling - Key Change

**Before:** Audio was returned inline as a base64-encoded string in `audio_base64`. Clients decoded this to play audio.

**After:** Audio is served from Supabase Storage. The `audio_url` field contains a public URL that can be used directly in an `<audio>` tag or fetched with an HTTP GET.

```diff
- const audioData = atob(response.forecast.audio_base64);
+ const audioUrl = response.forecast.audio_url;
+ // Use directly: <audio src={audioUrl} />
+ // Or fetch: const audioBlob = await fetch(audioUrl).then(r => r.blob());
```

---

## Field Rename Summary

For quick search-and-replace in client code:

| Search | Replace With |
|---|---|
| `.text` (forecast body) | `.content` |
| `.audio_base64` | `.audio_url` |
| `.picture_url` | `.image_url` |
| `.expired` (boolean) | `.is_expired` |
| `.language` (in history) | `.text_language` |
| `.instance` (in health) | `.supabase_url` |

---

## Unchanged

- `GET /` - Root endpoint (no changes)
- `GET /docs` - Swagger UI (no changes)
- Base URL and port remain the same
- Error response format (`status`, `message`) unchanged
- 404 behavior on missing forecast (triggers preparation) unchanged
