"""
Pydantic response models for API endpoints.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class ForecastMetadata(BaseModel):
    encoding: str
    language: Optional[str] = None
    locale: Optional[str] = None
    sizes: Dict[str, Optional[int]]


class ForecastData(BaseModel):
    id: str
    city: str
    content: str = Field(..., description="Forecast text content")
    forecast_at: str
    created_at: str
    expires_at: Optional[str] = None
    is_expired: bool
    age_seconds: int
    audio_url: Optional[str] = None
    audio_format: Optional[str] = None
    audio_size_bytes: Optional[int] = None
    image_url: Optional[str] = None
    image_format: Optional[str] = None
    image_size_bytes: Optional[int] = None
    metadata: ForecastMetadata
    record_metadata: Dict[str, Any]


class WeatherResponse(BaseModel):
    status: str = "success"
    city: str
    forecast: ForecastData


class WeatherNotFoundResponse(BaseModel):
    status: str = "error"
    message: str


class ForecastSummary(BaseModel):
    id: str
    city: str
    forecast_at: str
    created_at: Optional[str] = None
    expires_at: Optional[str] = None
    is_expired: bool
    text_language: Optional[str] = None
    text_size_bytes: Optional[int] = None
    has_audio: bool
    has_image: bool


class HistoryResponse(BaseModel):
    status: str = "success"
    city: Optional[str] = None
    count: int
    forecasts: List[ForecastSummary]


class CityDetail(BaseModel):
    image_url: Optional[str] = None


class StorageStatistics(BaseModel):
    total_forecasts: int
    total_text_bytes: int
    total_audio_bytes: int
    total_image_bytes: int
    forecasts_with_audio: int
    forecasts_with_images: int
    expired_forecasts: int
    cities_used: Dict[str, int]
    languages_used: Dict[str, int]
    active_cities: Dict[str, CityDetail] = {}


class StatsResponse(BaseModel):
    status: str = "success"
    statistics: StorageStatistics


class DatabaseHealth(BaseModel):
    connected: bool
    supabase_url: Optional[str] = None
    table_exists: Optional[bool] = None
    record_count: Optional[int] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    database: DatabaseHealth
    api_version: str


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[Dict[str, Any]] = None
