"""
generate_farmer_report tool. Wraps the existing, unmodified
report_service.generate_prediction_report + report_repository.create_report
— the same code path POST /api/reports/generate/{id} uses — so report
content and behavior stay identical whether triggered from the UI button
or asked for via the AI agent.
"""
from app.agent.tools.base import Tool, ToolContext, ToolResult
from app.core.config import settings
from app.repositories.prediction_repository import get_prediction_by_id, list_predictions_for_user
from app.repositories.report_repository import create_report
from app.services.report_service import generate_prediction_report


class GenerateFarmerReportTool(Tool):
    name = "generate_farmer_report"
    description = (
        "Generate a downloadable PDF farmer report for one of the farmer's crop "
        "predictions. If prediction_id is omitted, uses the most recent prediction."
    )
    parameters = {
        "type": "object",
        "properties": {
            "prediction_id": {
                "type": "string",
                "description": "ID of the prediction to report on. Omit to use the most recent one.",
            }
        },
        "required": [],
    }

    async def run(self, ctx: ToolContext, prediction_id: str = None, **kwargs) -> ToolResult:
        if prediction_id:
            prediction = get_prediction_by_id(ctx.db, prediction_id, ctx.current_user.id)
            if not prediction:
                return ToolResult.failure(
                    "No prediction with that ID was found for this user."
                )
        else:
            recent = list_predictions_for_user(ctx.db, ctx.current_user.id, sort_desc=True)
            if not recent:
                return ToolResult.failure(
                    "This farmer hasn't uploaded any crop images yet, so there's nothing to report on."
                )
            prediction = recent[0]

        try:
            filepath = generate_prediction_report(prediction, ctx.current_user, settings.REPORTS_DIR)
            report = create_report(ctx.db, ctx.current_user.id, prediction.id, filepath)
        except Exception as exc:  # pragma: no cover - defensive, mirrors API error handling
            return ToolResult.failure(f"Report generation failed: {exc}")

        return ToolResult.success(
            {
                "report_id": report.id,
                "prediction_id": prediction.id,
                "download_path": f"/api/reports/download/{report.id}",
            }
        )
