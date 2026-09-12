"""
Runs inference: real model if loaded, otherwise a clearly-labeled
deterministic fallback so the rest of the app remains testable end-to-end.
"""

import hashlib
from dataclasses import dataclass

from PIL import Image

from app.ml import model_loader
from app.ml.preprocessing import preprocess_for_model


@dataclass
class PredictionResult:
    disease: str
    confidence: float
    is_fallback: bool


def _severity_from_confidence_and_class(
    disease: str, confidence: float
) -> str:
    if "healthy" in disease.lower():
        return "Low"

    if confidence >= 0.85:
        return "High"

    if confidence >= 0.6:
        return "Medium"

    return "Low"


def predict(image: Image.Image) -> PredictionResult:
    """
    Run crop-disease inference.

    If a trained model is available, use the real model.
    If no trained model is available, use the deterministic
    development fallback.
    """

    # ---------------------------------------------------------
    # DEVELOPMENT FALLBACK
    # ---------------------------------------------------------
    if (
        model_loader.is_fallback_mode()
        or model_loader.get_model() is None
    ):
        # Get configured disease classes.
        class_names = model_loader.get_class_names()

        # During tests or certain startup paths, model_loader may
        # not have initialized the class names yet.
        if not class_names:
            model_loader.load_model()
            class_names = model_loader.get_class_names()

        # Never perform modulo by zero.
        if not class_names:
            raise RuntimeError("No disease classes are configured")

        # Deterministic fallback:
        # The same image always produces the same result.
        digest = hashlib.sha256(image.tobytes()).hexdigest()
        idx = int(digest, 16) % len(class_names)

        return PredictionResult(
            disease=class_names[idx],
            confidence=0.5,
            is_fallback=True,
        )

    # ---------------------------------------------------------
    # REAL MODEL INFERENCE
    # ---------------------------------------------------------
    import torch

    tensor = preprocess_for_model(image)

    with torch.no_grad():
        logits = model_loader.get_model()(tensor)

        probs = torch.softmax(logits, dim=1)[0]

        top_idx = int(torch.argmax(probs).item())

        confidence = float(probs[top_idx].item())

    # Get the class labels produced during model loading.
    class_names = model_loader.get_class_names()

    if top_idx < len(class_names):
        disease = class_names[top_idx]
    else:
        disease = "Unknown"

    return PredictionResult(
        disease=disease,
        confidence=confidence,
        is_fallback=False,
    )


def severity_for(
    disease: str,
    confidence: float,
) -> str:
    """
    Convert disease/confidence into a simple severity level.
    """
    return _severity_from_confidence_and_class(
        disease,
        confidence,
    )


def status_for(confidence: float, is_fallback: bool) -> str:
    """
    Classify a prediction as "fallback", "low_confidence", or "confident".

    Low-confidence real-model predictions are never presented to the user
    as a specific diagnosis — the caller (app/api/disease.py) uses this
    status to decide whether to show the full recommendation or a safe
    "unable to confidently identify" response instead.
    """
    from app.core.config import settings

    if is_fallback:
        return "fallback"
    if confidence < settings.CONFIDENCE_THRESHOLD:
        return "low_confidence"
    return "confident"