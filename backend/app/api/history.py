"""
Prediction history: list, search/filter/sort for the current user.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.repositories.prediction_repository import list_predictions_for_user
from app.schemas.prediction import PredictionHistoryItem


router = APIRouter(
    prefix="/history",
    tags=["History"],
)


def _parse_crop_and_disease(raw_class: str) -> tuple[str, str]:
    """
    Convert PlantVillage class names such as:

        Strawberry___Leaf_scorch

    into:

        Strawberry
        Leaf scorch
    """
    parts = raw_class.split("___")

    crop_raw = parts[0] if len(parts) > 1 else "Unknown"
    disease_raw = parts[-1] if len(parts) > 1 else raw_class

    crop_name = crop_raw.replace("_", " ").strip()
    disease_name = disease_raw.replace("_", " ").strip()

    return crop_name, disease_name


def _safe_history_item(prediction) -> dict:
    """
    Convert a database prediction into the safe representation used by
    the frontend History page.

    If the user-selected crop does not match the crop inferred by the
    model, do not present the model's disease as a confirmed diagnosis.
    """

    identified_crop, disease_label = _parse_crop_and_disease(
        prediction.disease
    )

    selected_crop = (prediction.crop or "").strip()

    crop_mismatch = (
        bool(selected_crop)
        and identified_crop.lower() not in (
            "unknown",
            selected_crop.lower(),
        )
    )

    if crop_mismatch:
        return {
            "id": prediction.id,
            "crop": selected_crop,
            "disease": "Unable to confidently identify",
            "confidence": round(prediction.confidence, 4),
            "severity": "Low",
            "created_at": prediction.created_at,
        }

    return {
        "id": prediction.id,
        "crop": selected_crop,
        "disease": disease_label,
        "confidence": round(prediction.confidence, 4),
        "severity": prediction.severity,
        "created_at": prediction.created_at,
    }


@router.get(
    "",
    response_model=list[PredictionHistoryItem],
)
def get_history(
    crop: Optional[str] = None,
    q: Optional[str] = Query(
        default=None,
        description="Search by disease name",
    ),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    sort: str = Query(
        default="latest",
        pattern="^(latest|oldest)$",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    predictions = list_predictions_for_user(
        db,
        current_user.id,
        crop=crop,
        date_from=date_from,
        date_to=date_to,
        sort_desc=(sort == "latest"),
        search=q,
    )

    return [
        _safe_history_item(prediction)
        for prediction in predictions
    ]