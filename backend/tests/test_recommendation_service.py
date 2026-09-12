from app.services.recommendation_service import get_recommendation, DISCLAIMER


def test_known_disease_returns_configured_guidance():
    rec = get_recommendation("Tomato___Early_blight")
    assert "blight" in rec["description"].lower()
    assert rec["treatment"]
    assert rec["prevention"]


def test_unknown_disease_returns_default_not_fabricated():
    rec = get_recommendation("Totally___Unknown_Disease")
    assert "consult" in rec["treatment"].lower()


def test_disclaimer_is_present_and_nontrivial():
    assert "informational purposes" in DISCLAIMER.lower()
