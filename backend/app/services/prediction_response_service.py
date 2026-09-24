"""
Builds the safe, user-facing PredictionOut representation of a stored
DiseasePrediction row.

This is a refactor-for-reuse, not new logic: the code below is moved
verbatim from app.api.disease.get_prediction's response-shaping steps
(crop-mismatch detection, low-confidence handling, recommendation lookup)
so that BOTH the GET /disease/{id} endpoint and the AI agent's
analyze_crop_image tool go through the exact same safety logic instead of
two copies that could silently drift apart. The ML inference itself
(app.ml.predictor) and the confidence-threshold logic (app.ml.predictor's
status_for/severity_for) are untouched.
"""
from typing import Optional
import json

from app.ml.predictor import status_for
from app.services.recommendation_service import (
    DISCLAIMER,
    get_recommendation,
    get_safe_recommendation,
    normalize_locale,
    normalize_context,
)
from app.schemas.prediction import PredictionOut

_LOW_CONFIDENCE_DESCRIPTION = (
    "The model could not confidently identify a disease from this image. "
    "This can happen if the leaf is healthy, the disease isn't one of "
    "GreenMind's 38 supported classes, or the photo quality (blur, poor "
    "lighting, multiple leaves, background clutter) is affecting the result."
)

def _parse_crop_and_disease(raw_class: str) -> tuple[str, str]:
    parts = raw_class.split("___")
    crop_raw = parts[0] if len(parts) > 1 else "Unknown"
    disease_raw = parts[-1] if len(parts) > 1 else raw_class
    crop = crop_raw.replace("_", " ").strip()
    disease = disease_raw.replace("_", " ").strip()
    return crop, disease


def build_prediction_response(prediction, locale: str = "en") -> PredictionOut:
    """
    prediction: a DiseasePrediction ORM row already confirmed to belong to
    the requesting user (ownership must be checked by the caller, e.g. via
    get_prediction_by_id(db, prediction_id, user_id), before this is called).
    """
    locale = normalize_locale(locale)
    context = normalize_context(
        json.loads(prediction.context_json)
        if getattr(prediction, "context_json", None)
        else None
    )
    identified_crop, disease_label = _parse_crop_and_disease(prediction.disease)

    pred_status = status_for(prediction.confidence, prediction.is_fallback_prediction)
    severity = prediction.severity

    crop_mismatch = (
        prediction.crop
        and identified_crop.lower() not in ("unknown", prediction.crop.lower())
    )

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
        possible_disease = f"{identified_crop} - {disease_label}"
        crop_mismatch_note = (
            f"You selected '{prediction.crop}', but the image was identified "
            f"as '{identified_crop}'. The result is not considered a reliable "
            f"diagnosis."
        )
        recommendation = get_safe_recommendation(locale)

    elif pred_status == "low_confidence":
        severity = "Low"
        display_disease = "Unable to confidently identify"
        description = _LOW_CONFIDENCE_DESCRIPTION
        possible_disease = f"{identified_crop} - {disease_label}"
        crop_mismatch_note = None
        recommendation = get_safe_recommendation(locale)

    else:
        display_disease = disease_label
        possible_disease = None
        crop_mismatch_note = None
        rec_data = get_recommendation(prediction.disease, locale=locale, context=context)
        description = rec_data.get("description", "")
        recommendation = rec_data

    return PredictionOut(
        id=prediction.id,
        crop=prediction.crop,
        disease=display_disease,
        confidence=round(prediction.confidence, 4),
        severity=severity,
        status=pred_status,
        description=description,
        is_fallback_prediction=prediction.is_fallback_prediction,
        disclaimer=DISCLAIMER,
        image_path=prediction.image_path,
        created_at=prediction.created_at,
        recommendation=recommendation,
        possible_disease=possible_disease,
        crop_mismatch_note=crop_mismatch_note,
        context=context,
    )
