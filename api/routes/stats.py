"""
Statistics endpoint.
"""
from fastapi import APIRouter

from api.models.responses import StatsResponse, ErrorResponse
from core.database import get_storage_stats
from core.exceptions import DatabaseConnectionError

router = APIRouter()


@router.get(
    "",
    response_model=StatsResponse,
    responses={
        200: {"description": "Successful response with storage statistics"},
        503: {"model": ErrorResponse, "description": "Database connection error"}
    },
    summary="Get storage statistics",
    description="Retrieves database storage statistics for weather forecasts"
)
async def get_stats():
    """Get storage statistics."""
    try:
        result = get_storage_stats()

        if result.get("status") == "error":
            raise DatabaseConnectionError(result.get("message", "Database error"))

        return {
            "status": "success",
            "statistics": {
                "total_forecasts": result["total_forecasts"],
                "total_text_bytes": result["total_text_bytes"],
                "total_audio_bytes": result["total_audio_bytes"],
                "total_image_bytes": result["total_image_bytes"],
                "forecasts_with_audio": result["forecasts_with_audio"],
                "forecasts_with_images": result["forecasts_with_images"],
                "expired_forecasts": result["expired_forecasts"],
                "cities_used": result["cities_used"],
                "languages_used": result["languages_used"],
                "active_cities": result["active_cities"],
            }
        }
    except DatabaseConnectionError:
        raise
    except Exception as e:
        raise DatabaseConnectionError(f"Unexpected error: {str(e)}")
