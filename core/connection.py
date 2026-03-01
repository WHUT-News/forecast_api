"""
Supabase connection management.
"""
from typing import Optional
from supabase import create_client, Client

from config import settings

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create the Supabase client instance."""
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL:
        raise ValueError("SUPABASE_URL environment variable is required")
    if not settings.SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")

    _supabase_client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )

    return _supabase_client


def reset_client() -> None:
    """Reset the global Supabase client instance."""
    global _supabase_client
    _supabase_client = None


def test_connection() -> dict:
    """Test Supabase connection by querying the weather_forecasts table."""
    try:
        client = get_supabase_client()
        result = client.table("weather_forecasts").select("id", count="exact").limit(1).execute()

        return {
            "connected": True,
            "supabase_url": settings.SUPABASE_URL,
            "table_exists": True,
            "record_count": result.count if result.count is not None else 0
        }
    except Exception as e:
        error_msg = str(e)
        if "does not exist" in error_msg.lower() or "relation" in error_msg.lower():
            return {
                "connected": True,
                "supabase_url": settings.SUPABASE_URL,
                "table_exists": False,
                "record_count": 0,
                "error": "weather_forecasts table does not exist. Run schema.sql."
            }

        return {
            "connected": False,
            "supabase_url": settings.SUPABASE_URL,
            "table_exists": False,
            "record_count": 0,
            "error": error_msg
        }
