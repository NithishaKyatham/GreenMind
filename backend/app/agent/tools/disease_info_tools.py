"""
get_disease_information and get_recommendations tools.

Both resolve a farmer-readable crop + disease name to GreenMind's raw
model class key (via recommendation_service.find_disease_class) and then
read the SAME recommendation_rules.json entry the disease-detection
pipeline itself uses — never a separately-authored answer that could
drift from what get_recommendation() gives a real prediction.

If the crop/disease combination isn't recognized, both tools return a
failure result rather than guessing, so the agent tells the farmer
honestly that GreenMind doesn't have specific guidance for that
combination instead of inventing agronomic advice.
"""
from app.agent.tools.base import Tool, ToolContext, ToolResult
from app.services.recommendation_service import find_disease_class, get_recommendation


def _lookup(crop: str, disease: str):
    disease_class = find_disease_class(crop, disease)
    if not disease_class:
        return None, ToolResult.failure(
            f"GreenMind doesn't have a specific disease named '{disease}' on '{crop}' in its "
            "38-class supported set. Suggest the farmer upload a leaf photo for image-based "
            "diagnosis instead of guessing from a text description."
        )
    return disease_class, None


class GetDiseaseInformationTool(Tool):
    name = "get_disease_information"
    description = (
        "Look up GreenMind's reference information about a specific crop disease "
        "(one of the 38 classes GreenMind's model is trained to detect) by crop and "
        "disease name."
    )
    parameters = {
        "type": "object",
        "properties": {
            "crop": {"type": "string", "description": "Crop name, e.g. 'Tomato'."},
            "disease": {"type": "string", "description": "Disease name, e.g. 'Early blight'."},
        },
        "required": ["crop", "disease"],
    }

    async def run(self, ctx: ToolContext, crop: str, disease: str, **kwargs) -> ToolResult:
        disease_class, failure = _lookup(crop, disease)
        if failure:
            return failure
        rec = get_recommendation(disease_class)
        return ToolResult.success({"crop": crop, "disease": disease, "description": rec.get("description", "")})


class GetRecommendationsTool(Tool):
    name = "get_recommendations"
    description = (
        "Get GreenMind's treatment, fertilizer, pesticide, prevention, crop management, "
        "and monitoring guidance for a specific crop disease (one of the 38 classes "
        "GreenMind's model is trained to detect)."
    )
    parameters = {
        "type": "object",
        "properties": {
            "crop": {"type": "string", "description": "Crop name, e.g. 'Tomato'."},
            "disease": {"type": "string", "description": "Disease name, e.g. 'Early blight'."},
        },
        "required": ["crop", "disease"],
    }

    async def run(self, ctx: ToolContext, crop: str, disease: str, **kwargs) -> ToolResult:
        disease_class, failure = _lookup(crop, disease)
        if failure:
            return failure
        rec = get_recommendation(disease_class)
        return ToolResult.success(
            {
                "crop": crop,
                "disease": disease,
                "treatment": rec.get("treatment"),
                "fertilizer": rec.get("fertilizer"),
                "pesticide_guidance": rec.get("pesticide_guidance"),
                "prevention": rec.get("prevention"),
                "crop_management": rec.get("crop_management"),
                "monitoring_advice": rec.get("monitoring_advice"),
            }
        )
