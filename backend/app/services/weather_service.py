
"""
Weather integration via OpenWeatherMap. Never fabricates data: if the API
key is missing or the request fails, returns a clearly-labeled
"unavailable" response instead of invented numbers.
"""

import logging
from datetime import datetime

import httpx

from app.core.config import settings

logger = logging.getLogger("greenmind.weather")


async def fetch_weather(location: str) -> dict:
    if not settings.WEATHER_API_KEY:
        return {
            "location": location,
            "temperature": None,
            "humidity": None,
            "rainfall": None,
            "condition": None,
            "wind_speed": None,
            "forecast": [],
            "source": "unavailable",
            "message": (
                "Weather API key is not configured. "
                "Set WEATHER_API_KEY in .env to enable live weather."
            ),
            "fetched_at": datetime.utcnow(),
        }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            geocode_url = settings.WEATHER_API_BASE_URL.replace(
                "/data/2.5", "/geo/1.0/direct"
            )
            geo_response = await client.get(
                geocode_url,
                params={
                    "q": location,
                    "limit": 1,
                    "appid": settings.WEATHER_API_KEY,
                },
            )
            geo_response.raise_for_status()
            geo_result = geo_response.json()

            if not geo_result:
                return _unavailable(
                    location,
                    "We could not find that city or town. Please check the location and try again.",
                )

            coordinates = geo_result[0]
            weather_params = {
                "lat": coordinates["lat"],
                "lon": coordinates["lon"],
                "appid": settings.WEATHER_API_KEY,
                "units": "metric",
            }

            current = await client.get(
                f"{settings.WEATHER_API_BASE_URL}/weather",
                params=weather_params,
            )

            current.raise_for_status()
            current_data = current.json()

            forecast_resp = await client.get(
                f"{settings.WEATHER_API_BASE_URL}/forecast",
                params=weather_params,
            )

            forecast_resp.raise_for_status()
            forecast_data = forecast_resp.json()

        forecast_days = _summarize_daily_forecast(
            forecast_data.get("list", [])
        )

        return {
            "location": location,
            "temperature": current_data.get("main", {}).get("temp"),
            "humidity": current_data.get("main", {}).get("humidity"),
            "rainfall": (
                current_data.get("rain", {}).get("1h", 0.0)
                if "rain" in current_data
                else 0.0
            ),
            "condition": (
                current_data.get("weather") or [{}]
            )[0].get("description"),
            "wind_speed": current_data.get("wind", {}).get("speed"),
            "forecast": forecast_days,
            "source": "live",
            "message": None,
            "fetched_at": datetime.utcnow(),
        }

    except httpx.HTTPStatusError as e:
        response_text = (
            e.response.text[:500]
            if e.response is not None
            else ""
        )

        logger.warning(
            "Weather API error: status=%s location=%s response=%s",
            e.response.status_code
            if e.response is not None
            else "unknown",
            location,
            response_text,
        )

        return _unavailable(
            location,
            "The weather service is temporarily unavailable. Please try again shortly.",
        )

    except httpx.RequestError:
        logger.exception(
            "Weather API request failed for location=%s",
            location,
        )

        return _unavailable(
            location,
            "The weather service is temporarily unreachable. "
            "Please try again shortly.",
        )


def _unavailable(location: str, message: str) -> dict:
    return {
        "location": location,
        "temperature": None,
        "humidity": None,
        "rainfall": None,
        "condition": None,
        "wind_speed": None,
        "forecast": [],
        "source": "unavailable",
        "message": message,
        "fetched_at": datetime.utcnow(),
    }


def _summarize_daily_forecast(three_hourly_list: list) -> list:
    """
    OpenWeatherMap's free /forecast endpoint returns 3-hour steps;
    collapse to daily min/max.
    """

    daily: dict = {}

    for entry in three_hourly_list:
        date_str = entry["dt_txt"].split(" ")[0]
        temp = entry["main"]["temp"]

        condition = (
            entry.get("weather") or [{}]
        )[0].get("description", "")

        pop = entry.get("pop", 0.0) * 100

        if date_str not in daily:
            daily[date_str] = {
                "temp_min": temp,
                "temp_max": temp,
                "condition": condition,
                "rain_probability": pop,
            }
        else:
            daily[date_str]["temp_min"] = min(
                daily[date_str]["temp_min"],
                temp,
            )

            daily[date_str]["temp_max"] = max(
                daily[date_str]["temp_max"],
                temp,
            )

            daily[date_str]["rain_probability"] = max(
                daily[date_str]["rain_probability"],
                pop,
            )

    return [
        {"date": date, **values}
        for date, values in list(daily.items())[:5]
    ]

