"""
get_seasonal_advice tool.

GreenMind has no per-location agricultural extension database, so this
tool intentionally does NOT try to give location-specific seasonal
predictions (which would require data GreenMind doesn't have, i.e.
fabrication). Instead it returns the standard, publicly-known Indian
cropping season calendar (Kharif/Rabi/Zaid) — general reference
information, explicitly labeled as such — so the agent can orient a
farmer's question ("what season is it, what's typically grown now")
without inventing location- or farm-specific advice it can't back up.

Months are given as calendar month numbers (1=January) for the typical
sowing-to-harvest window; actual dates vary by region and year, which the
`note` field says explicitly.
"""
from datetime import datetime, timezone

from app.agent.tools.base import Tool, ToolContext, ToolResult

_SEASONS = [
    {
        "name": "Kharif",
        "sowing_months": [6, 7],
        "harvest_months": [9, 10],
        "typical_crops": ["Rice", "Maize", "Soybean", "Cotton", "Groundnut"],
    },
    {
        "name": "Rabi",
        "sowing_months": [10, 11],
        "harvest_months": [3, 4],
        "typical_crops": ["Wheat", "Mustard", "Gram", "Potato", "Peas"],
    },
    {
        "name": "Zaid",
        "sowing_months": [3, 4],
        "harvest_months": [6, 7],
        "typical_crops": ["Watermelon", "Cucumber", "Fodder crops", "Vegetables"],
    },
]

_NOTE = (
    "This is general reference information about India's standard Kharif/Rabi/Zaid "
    "cropping calendar, not a location-specific forecast — actual sowing and harvest "
    "timing varies by region, local climate, and year. GreenMind doesn't have "
    "region-specific agricultural extension data."
)


def _months_between(season: dict) -> list:
    start = season["sowing_months"][0]
    end = season["harvest_months"][-1]
    if start <= end:
        return list(range(start, end + 1))
    return list(range(start, 13)) + list(range(1, end + 1))


def _current_season(month: int) -> str:
    for season in _SEASONS:
        if month in _months_between(season):
            return season["name"]
    return "Rabi"  # winter months fall within Rabi's growing window


class GetSeasonalAdviceTool(Tool):
    name = "get_seasonal_advice"
    description = (
        "Get general reference information about India's standard agricultural "
        "seasons (Kharif/Rabi/Zaid) — typical sowing/harvest windows and commonly "
        "grown crops. This is general public agricultural-calendar knowledge, NOT "
        "personalized or location-specific advice."
    )
    parameters = {"type": "object", "properties": {}, "required": []}

    async def run(self, ctx: ToolContext, **kwargs) -> ToolResult:
        now = datetime.now(timezone.utc)
        current = _current_season(now.month)
        return ToolResult.success(
            {
                "current_month": now.strftime("%B"),
                "likely_current_season": current,
                "seasons": _SEASONS,
                "note": _NOTE,
            }
        )
