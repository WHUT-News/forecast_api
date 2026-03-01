"""
Database connection wrapper for FastAPI.
Provides database operations using standalone modules.
"""
from .connection import get_supabase_client, reset_client, test_connection
from .forecast_operations import (
    get_cached_forecast,
    get_forecast_by_id,
    list_forecasts,
    get_storage_stats
)


def test_db_connection() -> dict:
    """Test database connection on startup."""
    return test_connection()


def cleanup_db_connection() -> None:
    """Reset the Supabase client on shutdown."""
    reset_client()


__all__ = [
    "get_supabase_client",
    "test_db_connection",
    "cleanup_db_connection",
    "get_cached_forecast",
    "get_forecast_by_id",
    "list_forecasts",
    "get_storage_stats"
]
