"""
Central registry of every tool the GreenMind agent can call. Adding a new
tool means writing a Tool subclass and adding one line here — nothing
else in the agent loop needs to change.
"""
from typing import Dict, List

from app.agent.tools.base import Tool
from app.agent.tools.analyze_crop_image import AnalyzeCropImageTool
from app.agent.tools.get_prediction_history import GetPredictionHistoryTool
from app.agent.tools.weather_tools import GetWeatherTool, GetWeatherForecastTool
from app.agent.tools.disease_info_tools import GetDiseaseInformationTool, GetRecommendationsTool
from app.agent.tools.get_crop_information import GetCropInformationTool
from app.agent.tools.get_seasonal_advice import GetSeasonalAdviceTool
from app.agent.tools.generate_farmer_report import GenerateFarmerReportTool

_TOOLS: List[Tool] = [
    AnalyzeCropImageTool(),
    GetPredictionHistoryTool(),
    GetWeatherTool(),
    GetWeatherForecastTool(),
    GetDiseaseInformationTool(),
    GetRecommendationsTool(),
    GetCropInformationTool(),
    GetSeasonalAdviceTool(),
    GenerateFarmerReportTool(),
]

TOOL_REGISTRY: Dict[str, Tool] = {tool.name: tool for tool in _TOOLS}


def get_tool(name: str) -> Tool | None:
    return TOOL_REGISTRY.get(name)


def all_tool_schemas() -> List[dict]:
    """Schemas for Anthropic's `tools` API parameter."""
    return [tool.schema() for tool in _TOOLS]
