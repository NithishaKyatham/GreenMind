"""
Tests for the AI Agent + tool-calling layer (app/agent/*).

Follows the existing test conventions in this suite: a fresh SQLite DB per
session (conftest.py's session-scoped setup_test_db fixture), inline
`_register_and_login(client, email=...)` helpers (same pattern as
test_disease_and_history.py / test_reports.py), and real Pillow-generated
fake images for prediction flows.

Two levels of testing, matching how the tools themselves are designed:
  - Pure unit tests: construct a ToolContext directly (a real DB session +
    a real User row already committed via the `client` fixture) and call
    tool.run(ctx, **kwargs) directly, no HTTP/LLM involved.
  - Integration tests: go through the real HTTP endpoint
    (POST /api/chatbot/message) with real Bearer-token auth via `client`,
    mocking only agent_service._call_anthropic (the one function that
    talks to the network) so the rest of the real request/auth/DB path
    runs unmocked.

No authentication or ownership check is ever bypassed or weakened to make
a test pass — the ownership tests specifically prove isolation holds.

Where a prediction needs a KNOWN status (crop-mismatch vs. matched-crop),
tests rely on the fact that ml/predictor.py's deterministic dev fallback
(ALLOW_MODEL_FALLBACK=true, no trained model, per conftest.py) hashes the
decoded image bytes to pick a class. For the standard 100x100 solid-green
JPEG used across this test suite (and elsewhere in the existing suite,
e.g. test_disease_and_history.py), that hash always resolves to
"Strawberry___Leaf_scorch" — verified by hand against
ml/models/class_names.json using the exact same decode path
(Image.open -> .verify() -> re-open -> .convert("RGB") -> .tobytes())
that app/ml/predictor.py uses. Selecting crop="tomato" against that image
therefore deterministically produces a crop-mismatch/low_confidence
result, and crop="strawberry" deterministically produces a matched-crop
result (still "fallback" status, since is_fallback_prediction is always
True in this test environment — fallback status takes priority over
confidence, per test_confidence_threshold.py).
"""
import io
import asyncio

import pytest
from PIL import Image

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.user import User
from app.agent import registry as agent_registry
from app.agent.tools.base import ToolContext
from app.agent.tools.analyze_crop_image import AnalyzeCropImageTool
from app.agent.tools.get_prediction_history import GetPredictionHistoryTool
from app.agent.tools.weather_tools import GetWeatherTool, GetWeatherForecastTool
from app.agent.tools.disease_info_tools import GetDiseaseInformationTool, GetRecommendationsTool
from app.agent import agent_service
from app.services.chatbot_service import _rule_based_reply
from app.services.recommendation_service import find_disease_class
from app.ml.predictor import predict


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _register_and_login(client, email="agent@example.com"):
    client.post(
        "/api/auth/register",
        json={"name": "Agent User", "email": email, "password": "SecurePass123"},
    )
    login = client.post("/api/auth/login", json={"email": email, "password": "SecurePass123"})
    return login.json()["access_token"]


def _fake_image_bytes():
    img = Image.new("RGB", (100, 100), color=(50, 150, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def _make_prediction(client, headers, crop="tomato"):
    response = client.post(
        "/api/disease/predict",
        headers=headers,
        data={"crop": crop},
        files={"image": ("leaf.jpg", _fake_image_bytes(), "image/jpeg")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _fixture_predicted_crop() -> str:
    """Return the fallback crop for the exact JPEG sent by _make_prediction."""
    with Image.open(_fake_image_bytes()) as image:
        disease = predict(image.convert("RGB")).disease
    return disease.split("___", 1)[0].replace("_", " ")


def _different_supported_crop(predicted_crop: str) -> str:
    for crop in ("tomato", "potato", "strawberry"):
        if crop.lower() != predicted_crop.lower():
            return crop
    raise AssertionError("Test crop choices must include a crop other than the fallback result")


def _ctx_for(email: str) -> ToolContext:
    db = SessionLocal()
    user = db.query(User).filter(User.email == email).first()
    return ToolContext(db=db, current_user=user)


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# 1 & 2. Tool registry / Anthropic tool schema generation
# ---------------------------------------------------------------------------

def test_tool_registry_contains_all_nine_expected_tools():
    expected = {
        "analyze_crop_image",
        "get_prediction_history",
        "get_weather",
        "get_weather_forecast",
        "get_disease_information",
        "get_recommendations",
        "get_crop_information",
        "get_seasonal_advice",
        "generate_farmer_report",
    }
    assert set(agent_registry.TOOL_REGISTRY.keys()) == expected


def test_anthropic_tool_schemas_are_generated_correctly():
    schemas = agent_registry.all_tool_schemas()
    assert len(schemas) == 9
    for schema in schemas:
        assert set(schema.keys()) == {"name", "description", "input_schema"}
        assert schema["name"] in agent_registry.TOOL_REGISTRY
        assert schema["description"]  # non-empty
        assert schema["input_schema"]["type"] == "object"
        assert "properties" in schema["input_schema"]
        # No tool schema may expose a user_id (or similar) parameter — the
        # LLM must never be able to specify whose data to operate on.
        assert "user_id" not in schema["input_schema"]["properties"]
        assert "user" not in schema["input_schema"]["properties"]
        assert "current_user" not in schema["input_schema"]["properties"]


def test_get_tool_returns_none_for_unknown_name():
    assert agent_registry.get_tool("delete_all_users") is None


# ---------------------------------------------------------------------------
# 3. Valid tool selection/execution (end-to-end through the HTTP endpoint,
#    with the outbound Anthropic call mocked)
# ---------------------------------------------------------------------------

def test_valid_tool_call_executes_and_feeds_result_back_to_model(client, monkeypatch):
    token = _register_and_login(client, email="toolcall1@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")

    calls = {"count": 0}

    async def fake_call(client_, messages, locale):
        calls["count"] += 1
        if calls["count"] == 1:
            assert any(t["name"] == "get_seasonal_advice" for t in agent_registry.all_tool_schemas())
            return {
                "content": [
                    {"type": "tool_use", "id": "toolu_abc", "name": "get_seasonal_advice", "input": {}}
                ]
            }
        return {"content": [{"type": "text", "text": "It's currently Kharif season."}]}

    monkeypatch.setattr(agent_service, "_call_anthropic", fake_call)

    response = client.post(
        "/api/chatbot/message", headers=headers, json={"message": "What season is it?"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "llm"
    assert data["reply"] == "It's currently Kharif season."
    assert data["tools_used"] == ["get_seasonal_advice"]


# ---------------------------------------------------------------------------
# 4. Current-user ownership / isolation
# ---------------------------------------------------------------------------

def test_analyze_crop_image_cannot_access_another_users_prediction(client):
    token_a = _register_and_login(client, email="owner_a@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    prediction_id = _make_prediction(client, headers_a, crop="tomato")

    _register_and_login(client, email="owner_b@example.com")

    ctx_b = _ctx_for("owner_b@example.com")
    result = _run(AnalyzeCropImageTool().run(ctx_b, prediction_id=prediction_id))
    ctx_b.db.close()

    assert result.ok is False
    assert result.data is None
    assert "not found" in result.error.lower() or "no prediction" in result.error.lower()


def test_get_prediction_history_only_returns_own_predictions(client):
    token_a = _register_and_login(client, email="hist_a@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    _make_prediction(client, headers_a, crop="tomato")

    token_b = _register_and_login(client, email="hist_b@example.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}
    _make_prediction(client, headers_b, crop="tomato")
    _make_prediction(client, headers_b, crop="tomato")

    ctx_b = _ctx_for("hist_b@example.com")
    result = _run(GetPredictionHistoryTool().run(ctx_b))
    ctx_b.db.close()

    assert result.ok is True
    assert result.data["count"] == 2  # not 3 — user A's prediction is excluded


def test_generate_farmer_report_cannot_target_another_users_prediction(client):
    from app.agent.tools.generate_farmer_report import GenerateFarmerReportTool

    token_a = _register_and_login(client, email="reportowner_a@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    prediction_id = _make_prediction(client, headers_a, crop="tomato")

    _register_and_login(client, email="reportowner_b@example.com")
    ctx_b = _ctx_for("reportowner_b@example.com")
    result = _run(GenerateFarmerReportTool().run(ctx_b, prediction_id=prediction_id))
    ctx_b.db.close()

    assert result.ok is False
    assert result.data is None


# ---------------------------------------------------------------------------
# 5. get_prediction_history (filtering + limit)
# ---------------------------------------------------------------------------

def test_get_prediction_history_crop_filter_and_limit(client):
    token = _register_and_login(client, email="hist_filter@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _make_prediction(client, headers, crop="tomato")
    _make_prediction(client, headers, crop="strawberry")

    ctx = _ctx_for("hist_filter@example.com")
    filtered = _run(GetPredictionHistoryTool().run(ctx, crop="tomato"))
    assert filtered.ok is True
    assert filtered.data["count"] == 1
    assert filtered.data["predictions"][0]["crop"] == "tomato"

    clamped = _run(GetPredictionHistoryTool().run(ctx, limit=999))
    assert clamped.ok is True
    assert clamped.data["count"] <= 20

    ctx.db.close()


# ---------------------------------------------------------------------------
# 6. get_weather
# ---------------------------------------------------------------------------

def test_get_weather_success(client, monkeypatch):
    _register_and_login(client, email="weather1@example.com")

    async def fake_fetch(location):
        return {
            "source": "live", "location": location, "temperature": 28.5,
            "humidity": 70, "rainfall": 0, "wind_speed": 3.2, "condition": "clear sky",
            "forecast": [], "message": None,
        }

    monkeypatch.setattr("app.agent.tools.weather_tools.fetch_weather", fake_fetch)

    ctx = _ctx_for("weather1@example.com")
    result = _run(GetWeatherTool().run(ctx, location="Warangal, Telangana, India"))
    ctx.db.close()

    assert result.ok is True
    assert result.data["temperature_c"] == 28.5
    assert result.data["condition"] == "clear sky"


def test_get_weather_unavailable_is_reported_not_fabricated(client, monkeypatch):
    _register_and_login(client, email="weather2@example.com")

    async def fake_fetch(location):
        return {
            "source": "unavailable", "location": location, "temperature": None,
            "humidity": None, "rainfall": None, "wind_speed": None, "condition": None,
            "forecast": [], "message": "Weather API key is not configured.",
        }

    monkeypatch.setattr("app.agent.tools.weather_tools.fetch_weather", fake_fetch)

    ctx = _ctx_for("weather2@example.com")
    result = _run(GetWeatherTool().run(ctx, location="Nowhere"))
    ctx.db.close()

    assert result.ok is False
    assert result.data is None
    assert "not configured" in result.error


# ---------------------------------------------------------------------------
# 7. get_weather_forecast
# ---------------------------------------------------------------------------

def test_get_weather_forecast_success(client, monkeypatch):
    _register_and_login(client, email="weather3@example.com")

    async def fake_fetch(location):
        return {
            "source": "live", "location": location, "temperature": 30, "humidity": 60,
            "rainfall": 0, "wind_speed": 2, "condition": "sunny",
            "forecast": [{"date": "2026-09-14", "temp_min": 22, "temp_max": 33, "condition": "sunny"}],
            "message": None,
        }

    monkeypatch.setattr("app.agent.tools.weather_tools.fetch_weather", fake_fetch)

    ctx = _ctx_for("weather3@example.com")
    result = _run(GetWeatherForecastTool().run(ctx, location="Hyderabad"))
    ctx.db.close()

    assert result.ok is True
    assert len(result.data["forecast"]) == 1


def test_get_weather_forecast_empty_forecast_is_a_failure_not_empty_success(client, monkeypatch):
    _register_and_login(client, email="weather4@example.com")

    async def fake_fetch(location):
        return {
            "source": "live", "location": location, "temperature": 30, "humidity": 60,
            "rainfall": 0, "wind_speed": 2, "condition": "sunny", "forecast": [], "message": None,
        }

    monkeypatch.setattr("app.agent.tools.weather_tools.fetch_weather", fake_fetch)

    ctx = _ctx_for("weather4@example.com")
    result = _run(GetWeatherForecastTool().run(ctx, location="Hyderabad"))
    ctx.db.close()

    assert result.ok is False


# ---------------------------------------------------------------------------
# 8. get_disease_information
# ---------------------------------------------------------------------------

def test_get_disease_information_known_disease(client):
    _register_and_login(client, email="diseaseinfo1@example.com")
    ctx = _ctx_for("diseaseinfo1@example.com")
    result = _run(GetDiseaseInformationTool().run(ctx, crop="Tomato", disease="Early blight"))
    ctx.db.close()

    assert result.ok is True
    assert result.data["description"]


def test_get_disease_information_unknown_combo_fails_honestly(client):
    _register_and_login(client, email="diseaseinfo2@example.com")
    ctx = _ctx_for("diseaseinfo2@example.com")
    result = _run(GetDiseaseInformationTool().run(ctx, crop="Dragonfruit", disease="Space Rot"))
    ctx.db.close()

    assert result.ok is False
    assert result.data is None


# ---------------------------------------------------------------------------
# 9. get_recommendations + find_disease_class resolution
# ---------------------------------------------------------------------------

def test_find_disease_class_resolves_known_crop_and_disease():
    assert find_disease_class("Tomato", "Early blight") == "Tomato___Early_blight"
    assert find_disease_class("tomato", "early blight") == "Tomato___Early_blight"


def test_find_disease_class_returns_none_for_unknown_combo():
    assert find_disease_class("Dragonfruit", "Space Rot") is None


def test_get_recommendations_known_disease(client):
    _register_and_login(client, email="rec1@example.com")
    ctx = _ctx_for("rec1@example.com")
    result = _run(GetRecommendationsTool().run(ctx, crop="Tomato", disease="Early blight"))
    ctx.db.close()

    assert result.ok is True
    assert result.data["treatment"]


def test_get_recommendations_unknown_disease_fails_honestly(client):
    _register_and_login(client, email="rec2@example.com")
    ctx = _ctx_for("rec2@example.com")
    result = _run(GetRecommendationsTool().run(ctx, crop="Tomato", disease="Space Blight From Mars"))
    ctx.db.close()

    assert result.ok is False
    assert result.data is None
    assert "38-class" in result.error or "doesn't have" in result.error


# ---------------------------------------------------------------------------
# 10. analyze_crop_image reuses build_prediction_response safety logic
# ---------------------------------------------------------------------------

def test_analyze_crop_image_matches_get_prediction_endpoint(client):
    token = _register_and_login(client, email="analyze1@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    prediction_id = _make_prediction(client, headers, crop="tomato")

    endpoint_response = client.get(f"/api/disease/{prediction_id}", headers=headers)
    assert endpoint_response.status_code == 200
    endpoint_data = endpoint_response.json()

    ctx = _ctx_for("analyze1@example.com")
    tool_result = _run(AnalyzeCropImageTool().run(ctx, prediction_id=prediction_id))
    ctx.db.close()

    assert tool_result.ok is True
    # The tool must produce EXACTLY the same safety-relevant fields as the
    # HTTP endpoint — proving it goes through build_prediction_response(),
    # not a second, potentially-diverging copy of the safety logic.
    for field in ("disease", "confidence", "severity", "status", "possible_disease", "crop_mismatch_note"):
        assert tool_result.data[field] == endpoint_data[field]


def test_analyze_crop_image_defaults_to_most_recent_when_no_id_given(client):
    token = _register_and_login(client, email="recent1@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    _make_prediction(client, headers, crop="tomato")
    latest_id = _make_prediction(client, headers, crop="tomato")

    ctx = _ctx_for("recent1@example.com")
    result = _run(AnalyzeCropImageTool().run(ctx))
    ctx.db.close()

    assert result.ok is True
    assert result.data["id"] == latest_id


def test_analyze_crop_image_reports_no_predictions_yet(client):
    _register_and_login(client, email="nopred@example.com")
    ctx = _ctx_for("nopred@example.com")
    result = _run(AnalyzeCropImageTool().run(ctx))
    ctx.db.close()

    assert result.ok is False
    assert "hasn't uploaded" in result.error


# ---------------------------------------------------------------------------
# 11. Low-confidence safety behavior (preserved through the tool)
# ---------------------------------------------------------------------------

def test_analyze_crop_image_low_confidence_is_flagged(client):
    token = _register_and_login(client, email="lowconf1@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    # tomato + the standard test image deterministically triggers a crop
    # mismatch, which is itself downgraded to low_confidence status (see
    # module docstring) — the two safety paths overlap for this fixture,
    # so this also exercises the low-confidence display fields directly.
    prediction_id = _make_prediction(client, headers, crop="tomato")

    ctx = _ctx_for("lowconf1@example.com")
    result = _run(AnalyzeCropImageTool().run(ctx, prediction_id=prediction_id))
    ctx.db.close()

    assert result.ok is True
    assert result.data["status"] == "low_confidence"
    assert result.data["disease"] == "Unable to confidently identify"
    assert result.data["possible_disease"] is not None
    # Low-confidence recommendation must be the safe generic one, never a
    # specific disease-targeted recommendation carried over unmodified.
    assert "No confident diagnosis" in result.data["recommendation"]["treatment"]


# ---------------------------------------------------------------------------
# 12. Crop-mismatch safety behavior
# ---------------------------------------------------------------------------

def test_analyze_crop_image_crop_mismatch_is_flagged(client):
    token = _register_and_login(client, email="mismatch1@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    predicted_crop = _fixture_predicted_crop()
    selected_crop = _different_supported_crop(predicted_crop)
    prediction_id = _make_prediction(client, headers, crop=selected_crop)

    ctx = _ctx_for("mismatch1@example.com")
    result = _run(AnalyzeCropImageTool().run(ctx, prediction_id=prediction_id))
    ctx.db.close()

    assert result.ok is True
    assert result.data["crop_mismatch_note"] is not None
    assert selected_crop in result.data["crop_mismatch_note"].lower()
    assert predicted_crop in result.data["possible_disease"]


def test_analyze_crop_image_matched_crop_is_not_flagged_mismatch(client):
    token = _register_and_login(client, email="matched1@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    # strawberry + the standard test image is a matched crop — no
    # crop-mismatch override should apply.
    prediction_id = _make_prediction(client, headers, crop=_fixture_predicted_crop())

    ctx = _ctx_for("matched1@example.com")
    result = _run(AnalyzeCropImageTool().run(ctx, prediction_id=prediction_id))
    ctx.db.close()

    assert result.ok is True
    assert result.data["crop_mismatch_note"] is None


# ---------------------------------------------------------------------------
# 13. Missing Anthropic API key -> exact existing rule_based_fallback
# ---------------------------------------------------------------------------

def test_missing_api_key_uses_exact_existing_rule_based_reply(client, monkeypatch):
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    token = _register_and_login(client, email="fallback1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    message = "What should I do for tomato blight?"
    response = client.post("/api/chatbot/message", headers=headers, json={"message": message})

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "rule_based_fallback"
    assert data["reply"] == _rule_based_reply(message)
    assert data["tools_used"] == []


# ---------------------------------------------------------------------------
# 14. LLM/tool-call failure -> safe rule-based fallback
# ---------------------------------------------------------------------------

def test_llm_call_failure_falls_back_safely(client, monkeypatch):
    token = _register_and_login(client, email="fallback2@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")

    async def failing_call(client_, messages, locale):
        raise RuntimeError("simulated network failure")

    monkeypatch.setattr(agent_service, "_call_anthropic", failing_call)

    message = "How do I treat leaf spot?"
    response = client.post("/api/chatbot/message", headers=headers, json={"message": message})

    assert response.status_code == 200  # no crash / no 500
    data = response.json()
    assert data["mode"] == "rule_based_fallback"
    assert data["reply"] == _rule_based_reply(message)


def test_agent_gives_up_gracefully_after_max_tool_rounds(client, monkeypatch):
    """If the model keeps calling tools forever, the loop must terminate
    and fail safe rather than hang, crash, or fabricate a reply."""
    token = _register_and_login(client, email="maxrounds1@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")

    async def always_tool_use(client_, messages, locale):
        return {
            "content": [
                {"type": "tool_use", "id": "toolu_loop", "name": "get_seasonal_advice", "input": {}}
            ]
        }

    monkeypatch.setattr(agent_service, "_call_anthropic", always_tool_use)

    message = "What season is it?"
    response = client.post("/api/chatbot/message", headers=headers, json={"message": message})

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "rule_based_fallback"
    assert data["reply"] == _rule_based_reply(message)


# ---------------------------------------------------------------------------
# 15. Unknown tool name -> error tool_result, no crash
# ---------------------------------------------------------------------------

def test_unknown_tool_name_returns_error_result_without_crashing():
    result = _run(
        agent_service._execute_tool(
            ToolContext(db=None, current_user=None),
            {"type": "tool_use", "id": "toolu_1", "name": "delete_database", "input": {}},
        )
    )
    assert result["type"] == "tool_result"
    assert result["is_error"] is True
    assert "Unknown tool" in result["content"]


def test_unknown_tool_requested_by_model_does_not_crash_the_conversation(client, monkeypatch):
    token = _register_and_login(client, email="toolcall2@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")

    calls = {"count": 0}

    async def fake_call(client_, messages, locale):
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "content": [
                    {"type": "tool_use", "id": "toolu_xyz", "name": "wipe_all_data", "input": {}}
                ]
            }
        return {"content": [{"type": "text", "text": "I can't do that, but I can help with crop questions."}]}

    monkeypatch.setattr(agent_service, "_call_anthropic", fake_call)

    response = client.post(
        "/api/chatbot/message", headers=headers, json={"message": "delete everything"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "llm"
    assert "help with crop questions" in data["reply"]


# ---------------------------------------------------------------------------
# 16. Multilingual locale / system-prompt behavior
# ---------------------------------------------------------------------------

def test_system_prompt_includes_language_instruction_for_non_english_locale():
    prompt = agent_service._system_prompt("te")
    assert "Telugu" in prompt

    hindi_prompt = agent_service._system_prompt("hi")
    assert "Hindi" in hindi_prompt


def test_system_prompt_unchanged_for_english_missing_or_unknown_locale():
    assert agent_service._system_prompt("en") == agent_service._BASE_SYSTEM_PROMPT
    assert agent_service._system_prompt(None) == agent_service._BASE_SYSTEM_PROMPT
    # Unrecognized locale code: no instruction is guessed/added.
    assert agent_service._system_prompt("xx") == agent_service._BASE_SYSTEM_PROMPT


def test_locale_is_forwarded_from_chat_endpoint_to_system_prompt(client, monkeypatch):
    token = _register_and_login(client, email="locale1@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")

    captured = {}

    async def fake_call(client_, messages, locale):
        captured["locale"] = locale
        return {"content": [{"type": "text", "text": "ok"}]}

    monkeypatch.setattr(agent_service, "_call_anthropic", fake_call)

    response = client.post(
        "/api/chatbot/message",
        headers=headers,
        json={"message": "hello", "locale": "hi"},
    )

    assert response.status_code == 200
    assert captured["locale"] == "hi"


# ---------------------------------------------------------------------------
# 17. tools_used response behavior
# ---------------------------------------------------------------------------

def test_tools_used_empty_in_rule_based_fallback_mode(client, monkeypatch):
    monkeypatch.setattr(settings, "AI_API_KEY", "")
    token = _register_and_login(client, email="tools_used_empty@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/api/chatbot/message", headers=headers, json={"message": "hello"})
    assert response.json()["tools_used"] == []


def test_tools_used_lists_every_tool_called_in_order(client, monkeypatch):
    token = _register_and_login(client, email="tools_used_multi@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    monkeypatch.setattr(settings, "AI_API_KEY", "test-key")

    async def fake_fetch(location):
        return {
            "source": "live", "location": location, "temperature": 25, "humidity": 50,
            "rainfall": 0, "wind_speed": 1, "condition": "clear", "forecast": [], "message": None,
        }

    monkeypatch.setattr("app.agent.tools.weather_tools.fetch_weather", fake_fetch)

    calls = {"count": 0}

    async def fake_call(client_, messages, locale):
        calls["count"] += 1
        if calls["count"] == 1:
            # Model calls two tools in the same round.
            return {
                "content": [
                    {"type": "tool_use", "id": "toolu_1", "name": "get_weather", "input": {"location": "Warangal"}},
                    {"type": "tool_use", "id": "toolu_2", "name": "get_seasonal_advice", "input": {}},
                ]
            }
        return {"content": [{"type": "text", "text": "Here's the weather and season info."}]}

    monkeypatch.setattr(agent_service, "_call_anthropic", fake_call)

    response = client.post(
        "/api/chatbot/message",
        headers=headers,
        json={"message": "weather and season?"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "llm"
    assert data["tools_used"] == ["get_weather", "get_seasonal_advice"]
