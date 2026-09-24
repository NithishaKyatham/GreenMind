from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Text

from app.core.database import Base
from app.models.base import gen_uuid


class WeatherRecord(Base):
    """Cached weather lookups, keyed by user + location, to avoid hammering the API."""
    __tablename__ = "weather_records"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    location = Column(String(255), nullable=False)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    rainfall = Column(Float, nullable=True)
    condition = Column(String(100), nullable=True)
    forecast_json = Column(Text, nullable=True)  # serialized multi-day forecast
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
