"""
analyze_crop_image tool.

IMPORTANT: this tool does NOT run new ML inference. Chat messages are
text; there is no image byte stream flowing through the agent's
tool-calling loop. The actual image upload + model inference happens
exclusively through the existing POST /api/disease/predict endpoint
(app.api.disease.predict_disease), which is untouched by this phase.

What this tool DOES do: given a prediction_id (or, if omitted, the
user's most recent prediction), return the same safe, non-fabricated
result that GET /api/disease/{id} would — via the shared
build_prediction_response() — so the agent can discuss an already-
computed diagnosis ("I analyzed the image you uploaded earlier...")
without ever inventing disease/confidence data of its own.
"""
from app.agent.tools.base import Tool, ToolContext, ToolResult
from app.repositories.prediction_repository import get_prediction_by_id, list_predictions_for_user
from app.services.prediction_response_service import build_prediction_response


class AnalyzeCropImageTool(Tool):
    name = "analyze_crop_image"
    description = (
        "Retrieve the AI diagnosis result for a crop image the farmer has already "
        "uploaded via the Diagnose Crop screen. Does not accept new image data — "
        "if the farmer hasn't uploaded a photo yet, ask them to do so instead of "
        "calling this tool. If prediction_id is omitted, returns the farmer's most "
        "recent prediction."
    )
    parameters = {
        "type": "object",
        "properties": {
            "prediction_id": {
                "type": "string",
                "description": "ID of a specific prediction to look up. Omit to use the most recent one.",
            }
        },
        "required": [],
    }

    async def run(self, ctx: ToolContext, prediction_id: str = None, **kwargs) -> ToolResult:
        if prediction_id:
            prediction = get_prediction_by_id(ctx.db, prediction_id, ctx.current_user.id)
            if not prediction:
                return ToolResult.failure(
                    "No prediction with that ID was found for this user. It may belong to "
                    "someone else, not exist, or have been mistyped."
                )
        else:
            recent = list_predictions_for_user(ctx.db, ctx.current_user.id, sort_desc=True)
            if not recent:
                return ToolResult.failure(
                    "This farmer hasn't uploaded any crop images yet. Ask them to use the "
                    "Diagnose Crop screen to upload a leaf photo first."
                )
            prediction = recent[0]

        result = build_prediction_response(prediction)
        return ToolResult.success(result.model_dump(mode="json"))
