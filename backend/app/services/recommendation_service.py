"""
Recommendation engine. Rules live in recommendation_rules.json (data, not
hardcoded in frontend or scattered through backend logic), so agricultural
content can be updated by editing the JSON without a code deploy.
"""
import json
import os
from typing import Optional

_RULES_PATH = os.path.join(os.path.dirname(__file__), "recommendation_rules.json")
_TRANSLATIONS_PATH = os.path.join(os.path.dirname(__file__), "recommendation_translations.json")

with open(_RULES_PATH) as f:
    _RULES = json.load(f)

with open(_TRANSLATIONS_PATH, encoding="utf-8") as f:
    _TRANSLATIONS = json.load(f)

SUPPORTED_LOCALES = frozenset({"en", "te", "hi", "ta", "kn", "mr", "ml", "bn", "gu", "pa"})

_SAFE_RECOMMENDATION = {
    "treatment": (
        "No confident diagnosis was made, so no specific treatment is "
        "recommended. If you're seeing visible symptoms, consult a local "
        "agricultural expert."
    ),
    "fertilizer": None,
    "pesticide_guidance": "Do not apply pesticides based on an unconfirmed diagnosis.",
    "prevention": (
        "Retake the photo: a single leaf, filling most of the frame, "
        "in even daylight, against a plain background usually improves results."
    ),
    "crop_management": None,
    "monitoring_advice": "Continue monitoring the plant and try again if new symptoms develop.",
}

DISCLAIMER = _RULES.get(
    "_disclaimer",
    "AI-generated guidance is for informational purposes. For severe crop "
    "damage or uncertain diagnosis, consult a qualified agricultural expert.",
)


def normalize_locale(locale: Optional[str]) -> str:
    normalized = (locale or "en").strip().lower().split("-")[0]
    return normalized if normalized in SUPPORTED_LOCALES else "en"


def _localized_entry(base: dict, locale: str, key: str) -> dict:
    localized = _TRANSLATIONS.get(locale, {}).get(key, {})
    return {**base, **localized}


def _normalize_context(context: Optional[dict]) -> dict:
    if not context:
        return {}

    normalized = {}
    for key in ("season", "region", "crop_stage", "soil_info"):
        value = context.get(key)
        if isinstance(value, str) and value.strip():
            normalized[key] = value.strip()

    weather = context.get("weather")
    if isinstance(weather, dict) and weather.get("source") == "live":
        normalized["weather"] = {
            "location": weather.get("location"),
            "temperature": weather.get("temperature"),
            "humidity": weather.get("humidity"),
            "rainfall": weather.get("rainfall"),
            "condition": weather.get("condition"),
            "forecast": weather.get("forecast") or [],
            "source": "live",
        }
    return normalized


def _add_context_guidance(recommendation: dict, context: dict) -> dict:
    """Add only transparent, deterministic notes to existing guidance fields."""
    notes = []
    provided = [
        ("season", "season"),
        ("crop_stage", "crop stage"),
        ("soil_info", "soil information"),
    ]
    provided_values = [f"{label}: {context[key]}" for key, label in provided if key in context]
    if provided_values:
        notes.append("Farmer-provided context: " + "; ".join(provided_values) + ".")

    weather = context.get("weather")
    if weather:
        rain_probability = max(
            (item.get("rain_probability", 0) for item in weather.get("forecast", []) if isinstance(item, dict)),
            default=0,
        )
        if rain_probability >= 50:
            notes.append(
                "Live weather context: rain is expected soon in the selected location. "
                "Review the prevention and monitoring guidance before field work."
            )
        else:
            notes.append(
                "Live weather context was available for this recommendation; "
                "no weather-specific rule was triggered."
            )

    if notes:
        existing = recommendation.get("monitoring_advice") or ""
        recommendation = {**recommendation, "monitoring_advice": " ".join([existing, *notes]).strip()}
    return recommendation


def get_recommendation(
    disease: str,
    severity: Optional[str] = None,
    locale: str = "en",
    context: Optional[dict] = None,
) -> dict:
    """
    Returns the structured recommendation dict for a given disease class.
    Falls back to a generic "consult an expert" response if the disease
    isn't in the configured rule set yet, rather than fabricating advice.
    """
    entry = _RULES.get("diseases", {}).get(disease)
    if entry is None:
        entry = _RULES["_default"]
    recommendation = _localized_entry(entry, normalize_locale(locale), disease)
    return _add_context_guidance(recommendation, _normalize_context(context))


def normalize_context(context: Optional[dict]) -> dict:
    """Return the small, JSON-safe context payload persisted with a prediction."""
    return _normalize_context(context)


def get_safe_recommendation(locale: str = "en") -> dict:
    """Return safe uncertainty guidance with per-field English fallback."""
    normalized = normalize_locale(locale)
    return _localized_entry(_SAFE_RECOMMENDATION, normalized, "_safe")
def find_disease_class(crop: str, disease: str) -> Optional[str]:
    """
    Resolve a human-readable crop + disease pair to the exact
    recommendation-rule/model class key.

    Returns None when there is no exact configured match.
    Never guesses.
    """
    target_crop = crop.strip().lower()
    target_disease = disease.strip().lower()

    for disease_class, entry in _RULES.get("diseases", {}).items():
        normalized_class = disease_class.replace("___", " - ").replace("_", " ").lower()

        if target_crop in normalized_class and target_disease in normalized_class:
            return disease_class

        entry_crop = str(entry.get("crop", "")).strip().lower()
        entry_disease = str(entry.get("disease", "")).strip().lower()

        if entry_crop == target_crop and entry_disease == target_disease:
            return disease_class

    return None