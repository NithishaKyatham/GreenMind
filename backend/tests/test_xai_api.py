import io
import os

from PIL import Image

from app.ml.predictor import PredictionResult
from app.services.xai_service import ExplanationResult


def _register_and_login(client, email):
    client.post(
        "/api/auth/register",
        json={"name": "XAI User", "email": email, "password": "SecurePass123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "SecurePass123"},
    )
    return response.json()["access_token"]


def _image():
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), color=(70, 150, 80)).save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer


def _create_prediction(client, token, monkeypatch, result):
    monkeypatch.setattr("app.api.disease.predict", lambda image: result)
    response = client.post(
        "/api/disease/predict",
        headers={"Authorization": f"Bearer {token}"},
        data={"crop": "Tomato"},
        files={"image": ("leaf.jpg", _image(), "image/jpeg")},
    )
    assert response.status_code == 201
    return response.json()


def test_xai_endpoint_returns_expected_structure_and_secure_image(client, monkeypatch):
    token = _register_and_login(client, "xai-success@example.com")
    prediction = _create_prediction(
        client,
        token,
        monkeypatch,
        PredictionResult("Tomato___Early_blight", 0.95, False),
    )
    monkeypatch.setattr(
        "app.api.xai.explain_image",
        lambda image, target: ExplanationResult(
            target_class=target,
            target_index=30,
            segments=[{"segment_id": 2, "weight": 0.31, "supports_prediction": True}],
            image_bytes=b"png-bytes",
        ),
    )

    response = client.post(
        f"/api/disease/{prediction['id']}/explanation",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["prediction_id"] == prediction["id"]
    assert data["target_class"] == "Tomato___Early_blight"
    assert data["target_label"] == "Early blight"
    assert data["method"] == "lime"
    assert data["segments"][0]["supports_prediction"] is True
    assert "local explanation" in data["disclaimer"]

    image_response = client.get(
        f"/api/disease/{prediction['id']}/explanation/image",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert image_response.status_code == 200
    assert image_response.content == b"png-bytes"


def test_xai_rejects_fallback_prediction(client, monkeypatch):
    token = _register_and_login(client, "xai-fallback@example.com")
    prediction = _create_prediction(
        client,
        token,
        monkeypatch,
        PredictionResult("Tomato___Early_blight", 0.5, True),
    )

    response = client.post(
        f"/api/disease/{prediction['id']}/explanation",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "fallback_prediction"


def test_xai_rejects_low_confidence_prediction(client, monkeypatch):
    token = _register_and_login(client, "xai-low@example.com")
    prediction = _create_prediction(
        client,
        token,
        monkeypatch,
        PredictionResult("Tomato___Early_blight", 0.59, False),
    )

    response = client.post(
        f"/api/disease/{prediction['id']}/explanation",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "low_confidence"


def test_xai_rejects_crop_mismatch(client, monkeypatch):
    token = _register_and_login(client, "xai-mismatch@example.com")
    prediction = _create_prediction(
        client,
        token,
        monkeypatch,
        PredictionResult("Potato___Late_blight", 0.95, False),
    )

    response = client.post(
        f"/api/disease/{prediction['id']}/explanation",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "crop_mismatch"


def test_xai_handles_missing_original_image(client, monkeypatch):
    token = _register_and_login(client, "xai-missing-image@example.com")
    prediction = _create_prediction(
        client,
        token,
        monkeypatch,
        PredictionResult("Tomato___Early_blight", 0.95, False),
    )
    os.remove(prediction["image_path"])

    response = client.post(
        f"/api/disease/{prediction['id']}/explanation",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "image_unavailable"


def test_xai_failure_returns_structured_error_without_affecting_prediction(client, monkeypatch):
    token = _register_and_login(client, "xai-failure@example.com")
    prediction = _create_prediction(
        client,
        token,
        monkeypatch,
        PredictionResult("Tomato___Early_blight", 0.95, False),
    )
    monkeypatch.setattr("app.api.xai.explain_image", lambda image, target: (_ for _ in ()).throw(RuntimeError("failed")))

    response = client.post(
        f"/api/disease/{prediction['id']}/explanation",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "explanation_unavailable"

    normal_prediction = client.get(
        f"/api/disease/{prediction['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert normal_prediction.status_code == 200


def test_xai_requires_prediction_ownership(client, monkeypatch):
    owner_token = _register_and_login(client, "xai-owner@example.com")
    other_token = _register_and_login(client, "xai-other@example.com")
    prediction = _create_prediction(
        client,
        owner_token,
        monkeypatch,
        PredictionResult("Tomato___Early_blight", 0.95, False),
    )

    response = client.post(
        f"/api/disease/{prediction['id']}/explanation",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "prediction_not_found"
