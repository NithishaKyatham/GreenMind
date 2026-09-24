
"""
Disease detection endpoint: image upload -> validation -> preprocessing ->
model inference (or labeled fallback) -> confidence/crop-safety check ->
recommendation lookup -> persisted prediction record.
"""

import os
import uuid
import logging
import json

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User
from app.ml.preprocessing import (
    validate_image,
    load_and_verify_image,
    ImageValidationError,
)
from app.ml.predictor import predict, severity_for, status_for
from app.services.recommendation_service import (
    DISCLAIMER,
    get_recommendation,
    get_safe_recommendation,
    normalize_locale,
    normalize_context,
)
from app.services.weather_service import fetch_weather
from app.services.prediction_response_service import build_prediction_response
from app.repositories.prediction_repository import (
    create_prediction,
    attach_recommendation,
    get_prediction_by_id,
)
from app.schemas.prediction import PredictionOut


router = APIRouter(
    prefix="/disease",
    tags=["Disease Detection"],
)

logger = logging.getLogger("greenmind.disease")


# ---------------------------------------------------------------------------
# Upload extension mapping
# ---------------------------------------------------------------------------
# The extension is derived from the validated content type instead of the
# user-supplied filename.
_CONTENT_TYPE_EXT = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
}


# ---------------------------------------------------------------------------
# Safe response for uncertain predictions
# ---------------------------------------------------------------------------
_LOW_CONFIDENCE_DESCRIPTION = (
    "The model could not confidently identify a disease from this image. "
    "This can happen if the leaf is healthy, the disease isn't one of "
    "GreenMind's 38 supported classes, or the photo quality (blur, poor "
    "lighting, multiple leaves, background clutter) is affecting the result."
)


# ---------------------------------------------------------------------------
# Fallback/demo response
# ---------------------------------------------------------------------------
_FALLBACK_DESCRIPTION = (
    "Development/demo mode: no trained model is loaded on this server, so "
    "this result is a deterministic placeholder, not a real AI diagnosis."
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _parse_crop_and_disease(raw_class: str) -> tuple[str, str]:
    """
    Convert model class names into readable crop and disease names.

    Example:
        Tomato___Early_blight
        -> ("Tomato", "Early blight")
    """

    parts = raw_class.split("___")

    crop_raw = parts[0] if len(parts) > 1 else "Unknown"
    disease_raw = parts[-1] if len(parts) > 1 else raw_class

    crop = crop_raw.replace("_", " ").strip()
    disease = disease_raw.replace("_", " ").strip()

    return crop, disease


# ---------------------------------------------------------------------------
# POST /api/disease/predict
# ---------------------------------------------------------------------------
@router.post(
    "/predict",
    response_model=PredictionOut,
    status_code=status.HTTP_201_CREATED,
)
async def predict_disease(
    crop: str = Form(
        ...,
        description="User-selected crop from the dropdown (used only as a hint)",
    ),
    locale: str = Form(
        "en",
        description="Selected application locale for localized recommendations",
    ),
    season: str | None = Form(None),
    region: str | None = Form(None),
    crop_stage: str | None = Form(None),
    soil_info: str | None = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    locale = normalize_locale(locale)
    # -----------------------------------------------------------------------
    # 1. Read uploaded image
    # -----------------------------------------------------------------------
    raw_bytes = await image.read()

    # -----------------------------------------------------------------------
    # 2. Validate and load image
    # -----------------------------------------------------------------------
    try:
        validate_image(
            image.filename or "upload",
            image.content_type or "",
            len(raw_bytes),
        )

        pil_image = load_and_verify_image(raw_bytes)

    except ImageValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # -----------------------------------------------------------------------
    # 3. AI model inference
    # -----------------------------------------------------------------------
    try:
        result = predict(pil_image)

    except Exception:
        logger.exception("Model inference failed")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The disease detection model is temporarily unavailable. "
                "Please try again shortly."
            ),
        )

    # -----------------------------------------------------------------------
    # 4. Store uploaded image safely
    # -----------------------------------------------------------------------
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    ext = _CONTENT_TYPE_EXT.get(
        (image.content_type or "").lower(),
        ".jpg",
    )

    stored_filename = f"{uuid.uuid4()}{ext}"
    stored_path = os.path.join(
        settings.UPLOAD_DIR,
        stored_filename,
    )

    with open(stored_path, "wb") as f:
        f.write(raw_bytes)

    # -----------------------------------------------------------------------
    # 5. Parse model result
    # -----------------------------------------------------------------------
    identified_crop, disease_label = _parse_crop_and_disease(
        result.disease
    )

    pred_status = status_for(
        result.confidence,
        result.is_fallback,
    )

    severity = severity_for(
        result.disease,
        result.confidence,
    )

    context = normalize_context({
        "season": season,
        "region": region or current_user.location,
        "crop_stage": crop_stage,
        "soil_info": soil_info,
    })
    weather_location = context.get("region")
    if weather_location:
        weather = await fetch_weather(weather_location)
        if weather.get("source") == "live":
            context["weather"] = weather

    # -----------------------------------------------------------------------
    # 6. Detect crop mismatch
    # -----------------------------------------------------------------------
    # Example:
    #
    # User selected:
    #     Apple
    #
    # Model predicted:
    #     Strawberry___Leaf_scorch
    #
    # We DO NOT trust the disease prediction in this situation.
    #
    # This prevents GreenMind from giving potentially dangerous treatment
    # recommendations for the wrong crop.
    crop_mismatch_note = None

    crop_mismatch = (
        bool(crop)
        and identified_crop.lower() not in (
            "unknown",
            crop.lower(),
        )
    )

    # -----------------------------------------------------------------------
    # 7. Build safe response
    # -----------------------------------------------------------------------
    if crop_mismatch:

        crop_mismatch_note = (
            f"You selected '{crop}', but the image was identified as "
            f"'{identified_crop}'. The result is not considered a reliable "
            f"diagnosis."
        )

        # IMPORTANT:
        # Treat crop mismatch as uncertain regardless of model confidence.
        pred_status = "low_confidence"
        severity = "Low"

        # Never give disease-specific treatment for a mismatch.
        rec_data = get_safe_recommendation(locale)

        description = (
            f"The selected crop is '{crop}', but the AI model detected "
            f"features associated with '{identified_crop}'. "
            "GreenMind cannot reliably diagnose this image. "
            "Please upload a clear photo of a single leaf in good lighting."
        )

        display_disease = "Unable to confidently identify"

        # Show what the model guessed only as a possibility,
        # NOT as a confirmed diagnosis.
        possible_disease = (
            f"{identified_crop} - {disease_label}"
        )

    # -----------------------------------------------------------------------
    # 8. Normal low-confidence result
    # -----------------------------------------------------------------------
    elif pred_status == "low_confidence":

        rec_data = get_safe_recommendation(locale)

        description = _LOW_CONFIDENCE_DESCRIPTION

        display_disease = "Unable to confidently identify"

        possible_disease = (
            f"{identified_crop} - {disease_label}"
        )

    # -----------------------------------------------------------------------
    # 9. Normal confident prediction
    # -----------------------------------------------------------------------
    else:

        rec_data = get_recommendation(
            result.disease,
            severity,
            locale,
            context,
        )

        description = rec_data.get(
            "description",
            "",
        )

        display_disease = disease_label

        possible_disease = None

        # Fallback mode should never be presented as a real AI diagnosis.
        if pred_status == "fallback":

            description = (
                f"{_FALLBACK_DESCRIPTION} "
                f"{description}"
            ).strip()

    # -----------------------------------------------------------------------
    # 10. Persist prediction
    # -----------------------------------------------------------------------
    prediction = create_prediction(
    db,
    user_id=current_user.id,
    # Store the crop selected by the user.
    # The model's detected crop is handled separately.
    crop=crop.strip(),
    image_path=stored_path,
    disease=result.disease,
    confidence=result.confidence,
    severity=severity,
    is_fallback=result.is_fallback,
    context_json=json.dumps(context),
)

    # -----------------------------------------------------------------------
    # 11. Persist recommendation
    # -----------------------------------------------------------------------
    attach_recommendation(
        db,
        prediction.id,
        rec_data,
    )

    db.refresh(prediction)

    # -----------------------------------------------------------------------
    # 12. Return API response
    # -----------------------------------------------------------------------
    return PredictionOut(
        id=prediction.id,
        crop=prediction.crop,
        disease=display_disease,
        confidence=round(
            prediction.confidence,
            4,
        ),
        severity=prediction.severity,
        status=pred_status,
        description=description,
        is_fallback_prediction=prediction.is_fallback_prediction,
        disclaimer=DISCLAIMER,
        image_path=prediction.image_path,
        created_at=prediction.created_at,
        recommendation=prediction.recommendation,
        possible_disease=possible_disease,
        crop_mismatch_note=crop_mismatch_note,
        context=context,
    )


# ---------------------------------------------------------------------------
# GET /api/disease/{prediction_id}
# ---------------------------------------------------------------------------
@router.get(
    "/{prediction_id}",
    response_model=PredictionOut,
)
def get_prediction(
    prediction_id: str,
    locale: str = Query("en", description="Selected application locale"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # -----------------------------------------------------------------------
    # 1. Find prediction belonging to current user
    # -----------------------------------------------------------------------
    prediction = get_prediction_by_id(
        db,
        prediction_id,
        current_user.id,
    )

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    # -----------------------------------------------------------------------
    # 2. Build the safe response.
    #
    # This logic (crop-mismatch detection, low-confidence handling,
    # recommendation lookup) is shared with the AI agent's
    # analyze_crop_image tool via prediction_response_service, so both
    # paths are guaranteed to apply the exact same safety behavior rather
    # than risking two copies drifting apart.
    # -----------------------------------------------------------------------
    return build_prediction_response(prediction, normalize_locale(locale))


@router.get("/{prediction_id}/image")
def get_prediction_image(
    prediction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Serves the uploaded leaf photo for a prediction. Authenticated and
    ownership-checked via the same get_prediction_by_id lookup as
    get_prediction — a plain static file mount was deliberately avoided
    here since that would let anyone with a guessable path view another
    user's photo.
    """
    prediction = get_prediction_by_id(
        db,
        prediction_id,
        current_user.id,
    )

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found",
        )

    if not prediction.image_path or not os.path.isfile(prediction.image_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    ext = os.path.splitext(prediction.image_path)[1].lower()
    media_type = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(
        ext, "application/octet-stream"
    )
    return FileResponse(prediction.image_path, media_type=media_type)

