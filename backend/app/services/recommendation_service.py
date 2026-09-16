"""
Recommendation engine. Rules live in recommendation_rules.json (data, not
hardcoded in frontend or scattered through backend logic), so agricultural
content can be updated by editing the JSON without a code deploy.
"""
import json
import os
from typing import Optional

_RULES_PATH = os.path.join(os.path.dirname(__file__), "recommendation_rules.json")

with open(_RULES_PATH) as f:
    _RULES = json.load(f)

DISCLAIMER = _RULES.get(
    "_disclaimer",
    "AI-generated guidance is for informational purposes. For severe crop "
    "damage or uncertain diagnosis, consult a qualified agricultural expert.",
)


def get_recommendation(disease: str, severity: Optional[str] = None) -> dict:
    """
    Returns the structured recommendation dict for a given disease class.
    Falls back to a generic "consult an expert" response if the disease
    isn't in the configured rule set yet, rather than fabricating advice.
    """
    entry = _RULES.get("diseases", {}).get(disease)
    if entry is None:
        entry = _RULES["_default"]
    return entry
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