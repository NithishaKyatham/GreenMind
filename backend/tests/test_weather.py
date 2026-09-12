from app.core.config import settings
def _register_and_login(client, email="weather@example.com"):
    client.post(
        "/api/auth/register",
        json={
            "name": "Weather User",
            "email": email,
            "password": "SecurePass123",
        },
    )
    login = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "SecurePass123",
        },
    )
    return login.json()["access_token"]


def test_weather_unavailable_without_api_key(client, monkeypatch):
    # Explicitly disable the API key for this test.
    monkeypatch.setattr(settings, "WEATHER_API_KEY", None)

    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(
        "/api/weather",
        headers=headers,
        params={"location": "Warangal, Telangana, India"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["source"] == "unavailable"
    assert data["temperature"] is None
    assert data["message"]