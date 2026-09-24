import io
from PIL import Image


def _register_and_login(client, email="report@example.com"):
    client.post("/api/auth/register", json={"name": "Report User", "email": email, "password": "SecurePass123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "SecurePass123"})
    return login.json()["access_token"]


def _make_prediction(client, headers):
    img = Image.new("RGB", (100, 100), color=(30, 120, 30))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    response = client.post(
        "/api/disease/predict", headers=headers,
        data={"crop": "tomato"}, files={"image": ("leaf.jpg", buf, "image/jpeg")},
    )
    return response.json()["id"]


def test_generate_and_download_report(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    prediction_id = _make_prediction(client, headers)

    gen = client.post(f"/api/reports/generate/{prediction_id}", headers=headers)
    assert gen.status_code == 201
    report_id = gen.json()["id"]

    download = client.get(f"/api/reports/download/{report_id}", headers=headers)
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert len(download.content) > 100  # a real, non-empty PDF was produced
