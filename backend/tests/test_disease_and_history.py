import io
from PIL import Image


def _register_and_login(client, email="crop@example.com"):
    client.post("/api/auth/register", json={"name": "Crop User", "email": email, "password": "SecurePass123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "SecurePass123"})
    return login.json()["access_token"]


def _fake_image_bytes():
    img = Image.new("RGB", (100, 100), color=(50, 150, 50))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_predict_disease_flow(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    img_buf = _fake_image_bytes()
    response = client.post(
        "/api/disease/predict",
        headers=headers,
        data={"crop": "tomato"},
        files={"image": ("leaf.jpg", img_buf, "image/jpeg")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["crop"] == "tomato"
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["severity"] in ("Low", "Medium", "High")
    assert data["disclaimer"]
    assert "recommendation" in data

    # History should now show this prediction
    history = client.get("/api/history", headers=headers)
    assert history.status_code == 200
    assert len(history.json()) >= 1


def test_predict_rejects_invalid_file(client):
    token = _register_and_login(client, email="badfile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    fake_txt = io.BytesIO(b"not an image")
    response = client.post(
        "/api/disease/predict",
        headers=headers,
        data={"crop": "tomato"},
        files={"image": ("notes.txt", fake_txt, "text/plain")},
    )
    assert response.status_code == 400


def test_crops_endpoint(client):
    token = _register_and_login(client, email="crops2@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/crops", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_crops_endpoint_matches_model_supported_crops(client):
    """The crop dropdown must only ever list crops the trained model supports."""
    import json, os
    token = _register_and_login(client, email="crops3@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/crops", headers=headers)
    assert response.status_code == 200
    returned_names = {c["name"] for c in response.json()}

    class_names_path = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models", "class_names.json")
    if os.path.exists(class_names_path):
        with open(class_names_path) as f:
            classes = json.load(f)
        expected_crops = {c.split("___")[0] for c in classes}
        assert returned_names == expected_crops
