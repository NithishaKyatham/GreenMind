"""
Central application configuration.
Reads from environment variables / .env file. Never hardcode secrets here.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    PROJECT_NAME: str = "GreenMind"
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = ""
    USE_SQLITE: bool = False
    SQLITE_PATH: str = "./greenmind_dev.db"

    # Auth
    JWT_SECRET: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Weather
    WEATHER_API_KEY: str = ""
    WEATHER_API_BASE_URL: str = "https://api.openweathermap.org/data/2.5"

    # AI Assistant
    AI_API_KEY: str = ""
    AI_API_PROVIDER: str = "anthropic"

    # ML Model
    MODEL_PATH: str = "../ml/models/crop_disease_model.pt"
    MODEL_ARCHITECTURE: str = "efficientnet_b0"
    MODEL_INPUT_SIZE: int = 224
    ALLOW_MODEL_FALLBACK: bool = True
    # Predictions below this confidence are reported as "low_confidence"
    # rather than a specific diagnosis — protects against confidently-wrong
    # answers on images the model wasn't trained to handle well.
    CONFIDENCE_THRESHOLD: float = 0.60

    # Uploads
    UPLOAD_DIR: str = "./uploads"
    REPORTS_DIR: str = "./reports"
    MAX_UPLOAD_SIZE_MB: int = 8

    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(
    env_file="../.env",
    env_file_encoding="utf-8",
    extra="ignore",
)
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.USE_SQLITE:
            return f"sqlite:///{self.SQLITE_PATH}"
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL must be set when USE_SQLITE is false.")
        return self.DATABASE_URL


settings = Settings()
