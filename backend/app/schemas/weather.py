from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ForecastDay(BaseModel):
    date: str
    temp_min: float
    temp_max: float
    condition: str
    rain_probability: Optional[float] = None


class WeatherOut(BaseModel):
    location: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    rainfall: Optional[float] = None
    condition: Optional[str] = None
    wind_speed: Optional[float] = None
    forecast: List[ForecastDay] = []
    source: str  # "live" | "unavailable"
    message: Optional[str] = None
    fetched_at: datetime
