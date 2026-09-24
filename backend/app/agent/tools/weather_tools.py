"""
get_weather and get_weather_forecast tools. Both call the existing,
unmodified fetch_weather() — which already never fabricates data (returns
source="unavailable" with an honest message on API failure/missing key)
— and simply present current-conditions vs. forecast-only views of the
same response.
"""
from app.agent.tools.base import Tool, ToolContext, ToolResult
from app.services.weather_service import fetch_weather


class GetWeatherTool(Tool):
    name = "get_weather"
    description = (
        "Get current weather conditions (temperature, humidity, rainfall, wind, "
        "condition) for a location. Never returns invented numbers — if live "
        "weather is unavailable, says so explicitly."
    )
    parameters = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City/village, state, country — e.g. 'Warangal, Telangana, India'.",
            }
        },
        "required": ["location"],
    }

    async def run(self, ctx: ToolContext, location: str, **kwargs) -> ToolResult:
        data = await fetch_weather(location)
        if data["source"] == "unavailable":
            return ToolResult.failure(data["message"] or "Weather data is currently unavailable.")
        return ToolResult.success(
            {
                "location": data["location"],
                "temperature_c": data["temperature"],
                "humidity_percent": data["humidity"],
                "rainfall_mm_1h": data["rainfall"],
                "wind_speed": data["wind_speed"],
                "condition": data["condition"],
            }
        )


class GetWeatherForecastTool(Tool):
    name = "get_weather_forecast"
    description = (
        "Get the multi-day weather forecast (temperature range, condition, rain "
        "probability per day) for a location. Never returns invented numbers — if "
        "the forecast is unavailable, says so explicitly."
    )
    parameters = {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City/village, state, country — e.g. 'Warangal, Telangana, India'.",
            }
        },
        "required": ["location"],
    }

    async def run(self, ctx: ToolContext, location: str, **kwargs) -> ToolResult:
        data = await fetch_weather(location)
        if data["source"] == "unavailable":
            return ToolResult.failure(data["message"] or "Weather forecast is currently unavailable.")
        if not data["forecast"]:
            return ToolResult.failure("No forecast data was returned for this location.")
        return ToolResult.success({"location": data["location"], "forecast": data["forecast"]})
