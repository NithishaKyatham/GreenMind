from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.weather import WeatherRecord
from app.services.weather_service import fetch_weather
from app.schemas.weather import WeatherOut
import json

router = APIRouter(prefix="/weather", tags=["Weather"])


@router.get("", response_model=WeatherOut)
async def get_weather(
    location: str = Query(..., description="e.g. 'Warangal, Telangana, India' or a city name"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await fetch_weather(location)

    if data["source"] == "live":
        record = WeatherRecord(
            user_id=current_user.id, location=location,
            temperature=data["temperature"], humidity=data["humidity"],
            rainfall=data["rainfall"], condition=data["condition"],
            forecast_json=json.dumps(data["forecast"]),
        )
        db.add(record)
        db.commit()

    return data
