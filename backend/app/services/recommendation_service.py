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
