from app.services.recommendation_service import (
    DISCLAIMER,
    get_recommendation,
    get_safe_recommendation,
)


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


def test_supported_locales_use_sparse_translations():
    assert "ప్రభావిత" in get_recommendation("Tomato___Early_blight", locale="te")["treatment"]
    assert "प्रभावित" in get_recommendation("Tomato___Early_blight", locale="hi")["treatment"]
    assert "பாதிக்கப்பட்ட" in get_recommendation("Tomato___Early_blight", locale="ta")["treatment"]
    assert "No treatment needed" in get_recommendation("Tomato___healthy", locale="en")["treatment"]


def test_missing_translation_field_falls_back_independently():
    recommendation = get_recommendation("Tomato___Late_blight", locale="te")
    assert "సోకిన" in recommendation["treatment"]
    assert recommendation["fertilizer"] == get_recommendation("Tomato___Late_blight")["fertilizer"]


def test_missing_or_unsupported_locale_falls_back_to_english():
    english = get_recommendation("Tomato___Late_blight")
    assert get_recommendation("Tomato___Late_blight", locale="kn") == english
    assert get_recommendation("Tomato___Early_blight", locale="xx") == get_recommendation("Tomato___Early_blight")


def test_safe_recommendation_is_non_empty_and_localized_when_available():
    safe = get_safe_recommendation("te")
    assert safe["treatment"]
    assert safe["pesticide_guidance"]
    assert "నమ్మదగిన" in safe["treatment"]


def test_disease_only_recommendation_is_unchanged():
    baseline = get_recommendation("Tomato___Early_blight")
    assert "Farmer-provided context" not in baseline["monitoring_advice"]
    assert "Live weather context" not in baseline["monitoring_advice"]


def test_disease_and_weather_adds_only_live_weather_context():
    rec = get_recommendation(
        "Tomato___Early_blight",
        context={
            "weather": {
                "source": "live",
                "location": "Warangal",
                "forecast": [{"rain_probability": 70}],
            }
        },
    )
    assert "Live weather context" in rec["monitoring_advice"]
    assert "rain is expected soon" in rec["monitoring_advice"]


def test_disease_and_season_is_explicitly_farmer_provided():
    rec = get_recommendation("Tomato___Early_blight", context={"season": "Kharif"})
    assert "Farmer-provided context: season: Kharif." in rec["monitoring_advice"]


def test_disease_and_crop_stage_is_explicitly_farmer_provided():
    rec = get_recommendation("Tomato___Early_blight", context={"crop_stage": "flowering"})
    assert "Farmer-provided context: crop stage: flowering." in rec["monitoring_advice"]


def test_multiple_contexts_are_combined_deterministically():
    rec = get_recommendation(
        "Tomato___Early_blight",
        context={
            "season": "Rabi",
            "crop_stage": "fruiting",
            "soil_info": "clay",
            "region": "Telangana",
            "weather": {"source": "live", "forecast": []},
        },
    )
    assert "season: Rabi" in rec["monitoring_advice"]
    assert "crop stage: fruiting" in rec["monitoring_advice"]
    assert "soil information: clay" in rec["monitoring_advice"]
    assert "Live weather context was available" in rec["monitoring_advice"]


def test_missing_optional_context_keeps_existing_recommendation():
    assert get_recommendation("Tomato___Early_blight", context={}) == get_recommendation("Tomato___Early_blight")


def test_unavailable_weather_is_not_treated_as_live_context():
    rec = get_recommendation(
        "Tomato___Early_blight",
        context={"weather": {"source": "unavailable", "forecast": []}},
    )
    assert "Live weather context" not in rec["monitoring_advice"]
