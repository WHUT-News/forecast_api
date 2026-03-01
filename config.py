"""
Configuration management for FastAPI server.
Loads settings from environment variables with validation.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    API_TITLE: str = "Weather Forecast API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "REST API for weather forecast retrieval"

    # Server Configuration
    PORT: int = 8200
    RELOAD: bool = False

    # CORS Configuration
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["GET", "OPTIONS"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str

    # Weather Agent URL Configuration
    WEATHER_AGENT_URL: str = "http://127.0.0.1:8200"

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
