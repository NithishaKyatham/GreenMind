"""Authenticated, on-demand LIME explanations for accepted predictions."""
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.ml.predictor import status_for
from app.models.user import User
from app.repositories.prediction_repository import get_prediction_by_id
from app.schemas.xai import ExplanationOut
from app.services.xai_service import (
    XAI_DISCLAIMER,
    explain_image,
    load_original_image,
)

router = APIRouter(prefix="/disease", tags=["Explainable AI"])


def _parse_crop(raw_class: str) -> str:
    parts = raw_class.split("___")
    return parts[0].replace("_", " ").strip() if len(parts) > 1 else "Unknown"


def _display_disease(raw_class: str) -> str:
    parts = raw_class.split("___")
    return parts[-1].replace("_", " ").strip() if len(parts) > 1 else raw_class


def _is_crop_mismatch(prediction) -> bool:
    selected_crop = (prediction.crop or "").strip().lower()
    identified_crop = _parse_crop(prediction.disease).lower()
    return bool(selected_crop and identified_crop not in ("unknown", selected_crop))


def _reject(code: str, message: str, http_status: int = status.HTTP_409_CONFLICT):
    raise HTTPException(status_code=http_status, detail={"code": code, "message": message})


@router.post(
    "/{prediction_id}/explanation",
    response_model=ExplanationOut,
    status_code=status.HTTP_200_OK,
)
def create_explanation(
    prediction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prediction = get_prediction_by_id(db, prediction_id, current_user.id)
    if not prediction:
        _reject("prediction_not_found", "Prediction not found.", status.HTTP_404_NOT_FOUND)

    if prediction.is_fallback_prediction:
        _reject("fallback_prediction", "Explanations are unavailable for fallback predictions.")
    if status_for(prediction.confidence, prediction.is_fallback_prediction) == "low_confidence":
        _reject("low_confidence", "Explanations are available only for accepted confident predictions.")
    if _is_crop_mismatch(prediction):
        _reject("crop_mismatch", "Explanations are unavailable when the selected and detected crops do not match.")

    try:
        image = load_original_image(prediction.image_path)
    except (FileNotFoundError, ValueError, OSError) as exc:
        _reject("image_unavailable", "The original prediction image cannot be safely retrieved.", status.HTTP_404_NOT_FOUND)

    try:
        explanation = explain_image(image, prediction.disease)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "explanation_unavailable", "message": "The LIME explanation could not be generated."},
        ) from exc

    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    image_path = Path(settings.REPORTS_DIR) / f"xai_{prediction.id}.png"
    image_path.write_bytes(explanation.image_bytes)

    return ExplanationOut(
        prediction_id=prediction.id,
        target_class=explanation.target_class,
        target_label=_display_disease(explanation.target_class),
        method="lime",
        segments=explanation.segments,
        explanation_image=f"/api/disease/{prediction.id}/explanation/image",
        disclaimer=XAI_DISCLAIMER,
    )


@router.get("/{prediction_id}/explanation/image")
def get_explanation_image(
    prediction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prediction = get_prediction_by_id(db, prediction_id, current_user.id)
    if not prediction:
        _reject("prediction_not_found", "Prediction not found.", status.HTTP_404_NOT_FOUND)

    image_path = Path(settings.REPORTS_DIR) / f"xai_{prediction.id}.png"
    if not image_path.is_file():
        _reject("explanation_not_found", "Generate the explanation before requesting its image.", status.HTTP_404_NOT_FOUND)

    return FileResponse(image_path, media_type="image/png", filename=image_path.name)
