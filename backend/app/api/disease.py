
"""
Disease detection endpoint: image upload -> validation -> preprocessing ->
model inference (or labeled fallback) -> confidence/crop-safety check ->
recommendation lookup -> persisted prediction record.
"""

import os
import uuid
import logging

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
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
from app.services.recommendation_service import get_recommendation, DISCLAIMER
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


_LOW_CONFIDENCE_RECOMMENDATION = {
    "treatment": (
        "No confident diagnosis was made, so no specific treatment is "
        "recommended. If you're seeing visible symptoms, consult a local "
        "agricultural expert."
    ),
    "fertilizer": None,
    "pesticide_guidance": (
        "Do not apply pesticides based on an unconfirmed diagnosis."
    ),
    "prevention": (
        "Retake the photo: a single leaf, filling most of the frame, "
        "in even daylight, against a plain background usually improves results."
    ),
    "crop_management": None,
    "monitoring_advice": (
        "Continue monitoring the plant and try again if new symptoms develop."
    ),
}


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
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
        rec_data = _LOW_CONFIDENCE_RECOMMENDATION

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

        rec_data = _LOW_CONFIDENCE_RECOMMENDATION

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
    # 2. Parse the model's original prediction
    # -----------------------------------------------------------------------
    identified_crop, disease_label = _parse_crop_and_disease(
        prediction.disease
    )

    # -----------------------------------------------------------------------
    # 3. Determine the normal prediction status
    # -----------------------------------------------------------------------
    pred_status = status_for(
        prediction.confidence,
        prediction.is_fallback_prediction,
    )

    severity = prediction.severity

    # -----------------------------------------------------------------------
    # 4. Detect crop mismatch
    # -----------------------------------------------------------------------
    # The database crop now contains the crop selected by the user.
    #
    # Example:
    #   Stored crop       = Apple
    #   Model prediction  = Strawberry___Leaf_scorch
    #
    # Therefore this is an uncertain result.
    crop_mismatch = (
        prediction.crop
        and identified_crop.lower() not in ("unknown", prediction.crop.lower())
    )

    # -----------------------------------------------------------------------
    # 5. Crop mismatch = unsafe to diagnose
    # -----------------------------------------------------------------------
    if crop_mismatch:

        pred_status = "low_confidence"
        severity = "Low"

        display_disease = "Unable to confidently identify"

        description = (
            f"The selected crop is '{prediction.crop}', but the AI model "
            f"detected features associated with '{identified_crop}'. "
            "GreenMind cannot reliably diagnose this image. "
            "Please upload a clear photo of a single leaf in good lighting."
        )

        possible_disease = (
            f"{identified_crop} - {disease_label}"
        )

        crop_mismatch_note = (
            f"You selected '{prediction.crop}', but the image was identified "
            f"as '{identified_crop}'. The result is not considered a reliable "
            f"diagnosis."
        )

    # -----------------------------------------------------------------------
    # 6. Normal low-confidence prediction
    # -----------------------------------------------------------------------
    elif pred_status == "low_confidence":

        severity = "Low"

        display_disease = "Unable to confidently identify"

        description = _LOW_CONFIDENCE_DESCRIPTION

        possible_disease = (
            f"{identified_crop} - {disease_label}"
        )

        crop_mismatch_note = None

    # -----------------------------------------------------------------------
    # 7. Normal confident prediction
    # -----------------------------------------------------------------------
    else:

        display_disease = disease_label

        possible_disease = None

        crop_mismatch_note = None

        rec_data = get_recommendation(
            prediction.disease
        )

        description = rec_data.get(
            "description",
            "",
        )

    # -----------------------------------------------------------------------
    # 8. Return safe prediction response
    # -----------------------------------------------------------------------
    return PredictionOut(
        id=prediction.id,

        # Always return the user's selected crop.
        crop=prediction.crop,

        disease=display_disease,

        confidence=round(
            prediction.confidence,
            4,
        ),

        severity=severity,

        status=pred_status,

        description=description,

        is_fallback_prediction=prediction.is_fallback_prediction,

        disclaimer=DISCLAIMER,

        image_path=prediction.image_path,

        created_at=prediction.created_at,

        # For mismatch/uncertain results, do NOT expose the stored
        # disease-specific recommendation as an active recommendation.
        recommendation=(
            _LOW_CONFIDENCE_RECOMMENDATION
            if pred_status == "low_confidence"
            else prediction.recommendation
        ),

        possible_disease=possible_disease,

        crop_mismatch_note=crop_mismatch_note,
    )

