"""
get_prediction_history tool. Reuses the exact same safe-history shaping
logic as GET /api/history (app.api.history._safe_history_item) rather
than duplicating the crop-mismatch handling a second time.
"""
from app.agent.tools.base import Tool, ToolContext, ToolResult
from app.api.history import _safe_history_item
from app.repositories.prediction_repository import list_predictions_for_user


class GetPredictionHistoryTool(Tool):
    name = "get_prediction_history"
    description = (
        "List the farmer's past crop disease predictions, most recent first. "
        "Optionally filter by crop name."
    )
    parameters = {
        "type": "object",
        "properties": {
            "crop": {"type": "string", "description": "Filter to a specific crop, e.g. 'Tomato'."},
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return (default 5, max 20).",
            },
        },
        "required": [],
    }

    async def run(self, ctx: ToolContext, crop: str = None, limit: int = 5, **kwargs) -> ToolResult:
        safe_limit = max(1, min(int(limit or 5), 20))
        predictions = list_predictions_for_user(ctx.db, ctx.current_user.id, crop=crop, sort_desc=True)
        items = [_safe_history_item(p) for p in predictions[:safe_limit]]
        return ToolResult.success({"count": len(items), "predictions": _jsonable(items)})


def _jsonable(items):
    # _safe_history_item returns plain dicts, but created_at is a datetime;
    # make it JSON-serializable for the tool_result payload sent to the LLM.
    out = []
    for item in items:
        out.append({**item, "created_at": item["created_at"].isoformat() if item.get("created_at") else None})
    return out
