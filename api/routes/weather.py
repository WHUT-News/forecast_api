"""
Weather forecast endpoints.
"""
from fastapi import APIRouter, Query, Path
from typing import Optional
import threading
import httpx
import logging
from datetime import datetime

from api.models.responses import (
    WeatherResponse,
    WeatherNotFoundResponse,
    HistoryResponse,
    ErrorResponse
)
from core.database import get_cached_forecast, list_forecasts
from core.exceptions import ForecastNotFoundError, DatabaseConnectionError
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

router = APIRouter()


def trigger_forecast_preparation(city: str, language: Optional[str] = None) -> None:
    """
    Trigger async forecast preparation using Weather Agent API.

    Args:
        city: City name to prepare forecast for
        language: Optional language code for the forecast
    """
    if not settings.WEATHER_AGENT_URL:
        logger.warning("WEATHER_AGENT_URL not configured, skipping forecast preparation")
        return

    try:
        def make_api_calls():
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                session_id = f"forecast_api_{city}_{language or 'en-US'}_{timestamp}"
                user_id = "forecast_api"

                language_spec = f" in {language}" if language else ""
                prompt = f"What is the current weather condition in {city}{language_spec}"

                with httpx.Client(timeout=60.0) as client:
                    session_url = (
                        f"{settings.WEATHER_AGENT_URL}/apps/weather_agent/users/{user_id}/sessions/{session_id}"
                    )
                    session_response = client.post(
                        session_url,
                        headers={"Content-Type": "application/json"},
                        json={}
                    )
                    session_response.raise_for_status()
                    logger.info(f"Created session {session_id} for {city}")

                    message_url = f"{settings.WEATHER_AGENT_URL}/run_sse"
                    message_payload = {
                        "appName": "weather_agent",
                        "userId": user_id,
                        "sessionId": session_id,
                        "newMessage": {
                            "role": "user",
                            "parts": [{"text": prompt}]
                        },
                        "streaming": False
                    }

                    message_response = client.post(
                        message_url,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "text/event-stream"
                        },
                        json=message_payload
                    )
                    message_response.raise_for_status()
                    logger.info(f"Sent forecast request for {city}")

            except Exception as e:
                logger.warning(f"Failed to trigger forecast for {city}: {str(e)}")

        thread = threading.Thread(target=make_api_calls, daemon=True)
        thread.start()

    except Exception as e:
        logger.warning(f"Failed to start forecast preparation for {city}: {str(e)}")


@router.get(
    "/{city}",
    response_model=WeatherResponse,
    responses={
        200: {"description": "Successful response with forecast data"},
        404: {"model": WeatherNotFoundResponse, "description": "Forecast not found - preparation triggered"},
        503: {"model": ErrorResponse, "description": "Database connection error"}
    },
    summary="Get latest forecast for a city",
    description="Retrieves the most recent valid (non-expired) forecast for the specified city"
)
async def get_latest_forecast(
    city: str = Path(..., description="City name (case-insensitive)"),
    language: Optional[str] = Query(None, description="ISO 639-1 language code filter"),
    include_expired: bool = Query(False, description="Include expired forecasts")
):
    """Get the latest forecast for a city."""
    try:
        result = get_cached_forecast(city, language, include_expired)

        if not result.get("found"):
            logger.info(f"No forecast found for {city}, triggering preparation")
            trigger_forecast_preparation(city, language)
            raise ForecastNotFoundError(
                f"Forecast for {city} is being prepared. Please try again shortly."
            )

        return {
            "status": "success",
            "city": city.lower(),
            "forecast": result["forecast"]
        }
    except ForecastNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_latest_forecast: {str(e)}", exc_info=True)
        raise DatabaseConnectionError(f"Database error: {str(e)}")


@router.get(
    "/{city}/history",
    response_model=HistoryResponse,
    responses={
        200: {"description": "Successful response with forecast history"},
        503: {"model": ErrorResponse, "description": "Database connection error"}
    },
    summary="Get forecast history for a city",
    description="Retrieves historical forecasts for a city with optional filtering"
)
async def get_forecast_history(
    city: str = Path(..., description="City name"),
    language: Optional[str] = Query(None, description="ISO 639-1 language code filter"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Results offset for pagination"),
    include_expired: bool = Query(False, description="Include expired forecasts")
):
    """Get forecast history for a city."""
    try:
        result = list_forecasts(
            city=city,
            language=language,
            include_expired=include_expired,
            limit=limit,
            offset=offset
        )

        return {
            "status": "success",
            "city": city.lower(),
            "count": len(result.get("forecasts", [])),
            "forecasts": result.get("forecasts", [])
        }
    except Exception as e:
        raise DatabaseConnectionError(f"Database error: {str(e)}")
