"""
get_crop_information tool.

GreenMind's database only stores a crop's name and display names — it has
no growing-season, water-requirement, or soil-type data. Rather than
having the LLM invent agronomic specifics (which the "never fabricate"
requirement rules out), this tool reports only what GreenMind actually
knows and can verify: whether the crop is supported, and which specific
diseases the trained model can detect for it. Anything beyond that is
explicitly out of scope for this tool and the system prompt tells the
model not to present invented specifics as GreenMind data.
"""
from app.agent.tools.base import Tool, ToolContext, ToolResult
from app.api.crops import ensure_crops_seeded
from app.models.crop import Crop
from app.ml import model_loader


class GetCropInformationTool(Tool):
    name = "get_crop_information"
    description = (
        "Look up which crops GreenMind supports and which specific diseases the "
        "trained model can detect for a given crop. Does NOT provide growing-season, "
        "soil, or water-requirement data — GreenMind doesn't have that in its database."
    )
    parameters = {
        "type": "object",
        "properties": {
            "crop": {"type": "string", "description": "Crop name, e.g. 'Tomato'."},
        },
        "required": ["crop"],
    }

    async def run(self, ctx: ToolContext, crop: str, **kwargs) -> ToolResult:
        ensure_crops_seeded(ctx.db)
        crop_norm = crop.strip().lower()
        row = (
            ctx.db.query(Crop)
            .filter(Crop.display_name_en.ilike(crop_norm) | Crop.name.ilike(f"%{crop_norm}%"))
            .first()
        )
        if not row:
            return ToolResult.failure(
                f"'{crop}' isn't one of GreenMind's supported crops. GreenMind's disease "
                "detector only covers the 14 crops it was trained on."
            )

        class_names = model_loader.get_class_names() or []
        diseases = []
        for class_name in class_names:
            if not class_name.lower().startswith(row.name.lower()):
                continue
            parts = class_name.split("___")
            disease_label = parts[-1].replace("_", " ").strip() if len(parts) > 1 else class_name
            diseases.append(disease_label)

        return ToolResult.success(
            {
                "crop": row.display_name_en,
                "supported": True,
                "detectable_diseases": diseases,
            }
        )
