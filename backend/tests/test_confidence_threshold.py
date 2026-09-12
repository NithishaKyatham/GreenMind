"""
Pure unit tests for the confidence-threshold / status logic — no model or
DB needed, so these run regardless of whether a trained model is present.
"""
from app.ml.predictor import status_for


def test_fallback_status_takes_priority():
    # Even a "high" confidence fallback prediction must be labeled fallback,
    # never presented as if it came from the real model.
    assert status_for(confidence=0.99, is_fallback=True) == "fallback"


def test_low_confidence_below_threshold():
    assert status_for(confidence=0.10, is_fallback=False) == "low_confidence"


def test_confident_at_or_above_threshold():
    from app.core.config import settings
    assert status_for(confidence=settings.CONFIDENCE_THRESHOLD, is_fallback=False) == "confident"
    assert status_for(confidence=0.99, is_fallback=False) == "confident"
