"""
Forecast operations for Supabase.
"""
import base64
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from .connection import get_supabase_client
from .encoding import decode_text


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _decode_bytea(value: Optional[str], encoding: str) -> Optional[str]:
    if value is None:
        return None

    if isinstance(value, bytes):
        return decode_text(value, encoding)

    if isinstance(value, str):
        text = value
        if text.startswith("\\x") or text.startswith("0x"):
            try:
                raw = bytes.fromhex(text[2:])
                return decode_text(raw, encoding)
            except Exception:
                return text

        try:
            padding = (4 - len(text) % 4) % 4
            raw = base64.b64decode(text + "=" * padding)
            return decode_text(raw, encoding)
        except Exception:
            return text

    return str(value)


def _parse_record(record: Dict[str, Any]) -> Dict[str, Any]:
    encoding = record.get("text_encoding") or "utf-8"
    content = _decode_bytea(record.get("forecast_text"), encoding) or ""

    created_at = record.get("created_at") or record.get("forecast_at")
    created_dt = _parse_timestamp(created_at)
    age_seconds = 0
    if created_dt:
        age_seconds = int((datetime.now(timezone.utc) - created_dt).total_seconds())

    is_expired = False
    if record.get("expires_at"):
        expires_dt = _parse_timestamp(record.get("expires_at"))
        if expires_dt:
            is_expired = datetime.now(timezone.utc) > expires_dt

    return {
        "id": record.get("id"),
        "city": record.get("city"),
        "content": content,
        "forecast_at": record.get("forecast_at"),
        "created_at": record.get("created_at") or record.get("forecast_at"),
        "expires_at": record.get("expires_at"),
        "is_expired": is_expired,
        "age_seconds": age_seconds,
        "audio_url": record.get("audio_url"),
        "audio_format": record.get("audio_format"),
        "audio_size_bytes": record.get("audio_size_bytes"),
        "image_url": record.get("image_url"),
        "image_format": record.get("image_format"),
        "image_size_bytes": record.get("image_size_bytes"),
        "metadata": {
            "encoding": encoding,
            "language": record.get("text_language"),
            "locale": record.get("text_locale"),
            "sizes": {
                "text": record.get("text_size_bytes"),
                "audio": record.get("audio_size_bytes"),
                "image": record.get("image_size_bytes")
            }
        },
        "record_metadata": record.get("metadata", {}) or {}
    }


def get_forecast_by_id(forecast_id: str) -> Dict[str, Any]:
    client = get_supabase_client()

    result = (
        client.table("weather_forecasts")
        .select("*")
        .eq("id", forecast_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        return {"found": False}

    return {"found": True, "forecast": _parse_record(result.data[0])}


def get_cached_forecast(
    city: str,
    language: Optional[str] = None,
    include_expired: bool = False
) -> Dict[str, Any]:
    client = get_supabase_client()

    query = client.table("weather_forecasts").select("*").ilike("city", city)

    if language:
        query = query.eq("text_language", language)
    if not include_expired:
        query = query.or_("expires_at.is.null,expires_at.gt.now()")

    query = query.order("forecast_at", desc=True).limit(1)
    result = query.execute()

    if not result.data:
        return {"found": False}

    return {"found": True, "forecast": _parse_record(result.data[0])}


def list_forecasts(
    city: Optional[str] = None,
    language: Optional[str] = None,
    include_expired: bool = False,
    limit: int = 10,
    offset: int = 0
) -> Dict[str, Any]:
    client = get_supabase_client()

    query = client.table("weather_forecasts").select(
        "id, city, forecast_at, created_at, expires_at, "
        "text_size_bytes, text_language, audio_url, image_url"
    )

    if city:
        query = query.ilike("city", city)
    if language:
        query = query.eq("text_language", language)
    if not include_expired:
        query = query.or_("expires_at.is.null,expires_at.gt.now()")

    query = query.order("forecast_at", desc=True).range(offset, offset + limit - 1)
    result = query.execute()

    forecasts = []
    for record in result.data:
        is_expired = False
        if record.get("expires_at"):
            expires_dt = _parse_timestamp(record.get("expires_at"))
            if expires_dt:
                is_expired = datetime.now(timezone.utc) > expires_dt

        forecasts.append({
            "id": record.get("id"),
            "city": record.get("city"),
            "forecast_at": record.get("forecast_at"),
            "created_at": record.get("created_at"),
            "expires_at": record.get("expires_at"),
            "is_expired": is_expired,
            "text_language": record.get("text_language"),
            "text_size_bytes": record.get("text_size_bytes"),
            "has_audio": record.get("audio_url") is not None,
            "has_image": record.get("image_url") is not None,
        })

    return {"status": "success", "forecasts": forecasts}


def get_storage_stats() -> Dict[str, Any]:
    client = get_supabase_client()

    try:
        result = client.rpc("get_forecast_storage_stats").execute()
        if result.data:
            data = result.data[0] if isinstance(result.data, list) else result.data
            return {
                "status": "success",
                "total_forecasts": int(data.get("total_forecasts", 0)),
                "total_text_bytes": int(data.get("total_text_bytes", 0)),
                "total_audio_bytes": int(data.get("total_audio_bytes", 0)),
                "total_image_bytes": int(data.get("total_image_bytes", 0)),
                "forecasts_with_audio": int(data.get("forecasts_with_audio", 0)),
                "forecasts_with_images": int(data.get("forecasts_with_images", 0)),
                "expired_forecasts": int(data.get("expired_forecasts", 0)),
                "cities_used": data.get("cities_used", {}) or {},
                "languages_used": data.get("languages_used", {}) or {}
            }
    except Exception:
        pass

    try:
        result = client.table("weather_forecasts").select(
            "id, text_size_bytes, audio_size_bytes, image_size_bytes, "
            "audio_url, image_url, expires_at, city, text_language"
        ).execute()

        records = result.data
        if not records:
            return {
                "status": "success",
                "total_forecasts": 0,
                "total_text_bytes": 0,
                "total_audio_bytes": 0,
                "total_image_bytes": 0,
                "forecasts_with_audio": 0,
                "forecasts_with_images": 0,
                "expired_forecasts": 0,
                "cities_used": {},
                "languages_used": {}
            }

        now = datetime.now(timezone.utc)
        stats = {
            "total_forecasts": len(records),
            "total_text_bytes": sum(r.get("text_size_bytes") or 0 for r in records),
            "total_audio_bytes": sum(r.get("audio_size_bytes") or 0 for r in records),
            "total_image_bytes": sum(r.get("image_size_bytes") or 0 for r in records),
            "forecasts_with_audio": sum(1 for r in records if r.get("audio_url")),
            "forecasts_with_images": sum(1 for r in records if r.get("image_url")),
            "expired_forecasts": 0,
            "cities_used": {},
            "languages_used": {}
        }

        for record in records:
            if record.get("expires_at"):
                exp = _parse_timestamp(record.get("expires_at"))
                if exp and now > exp:
                    stats["expired_forecasts"] += 1

            city = record.get("city")
            if city:
                stats["cities_used"][city] = stats["cities_used"].get(city, 0) + 1

            language = record.get("text_language")
            if language:
                stats["languages_used"][language] = stats["languages_used"].get(language, 0) + 1

        return {"status": "success", **stats}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get stats: {e}"}
