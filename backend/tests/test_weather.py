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

# ---------------------------------------------------------------------------
# Geocode-then-coordinates flow (fixes: bare state names like "Telangana"
# returning a raw 404 from OpenWeather's name-only lookup).
# ---------------------------------------------------------------------------
import httpx
import json


class _FakeGeoResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code
        # weather_service.py's error handler reads e.response.text — a
        # real httpx.Response always has this, so the fake must too or
        # the exception-handling path itself would blow up with an
        # AttributeError instead of degrading gracefully as intended.
        self.text = json.dumps(json_data)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)

    def json(self):
        return self._json_data


def _fake_get_factory(geo_result, weather_status=200, forecast_status=200):
    """
    Builds a fake httpx.AsyncClient.get that routes by URL: the geocoding
    call returns `geo_result` (a list, possibly empty), and the weather /
    forecast calls succeed or fail per the given status codes. This lets
    each test simulate exactly one stage failing without mocking the
    entire client.
    """

    async def fake_get(self, url, params=None):
        if "/geo/1.0/direct" in url:
            return _FakeGeoResponse(geo_result)
        if url.endswith("/weather"):
            if weather_status >= 400:
                return _FakeGeoResponse({}, status_code=weather_status)
            return _FakeGeoResponse(
                {
                    "main": {"temp": 29.0, "humidity": 55},
                    "weather": [{"description": "clear sky"}],
                    "wind": {"speed": 2.1},
                }
            )
        if url.endswith("/forecast"):
            if forecast_status >= 400:
                return _FakeGeoResponse({}, status_code=forecast_status)
            return _FakeGeoResponse({"list": []})
        raise AssertionError(f"Unexpected weather-service URL: {url}")

    return fake_get


def test_weather_resolves_state_only_location_via_geocoding(client, monkeypatch):
    """
    A bare state name like "Telangana" has no direct city-name match in
    OpenWeather's weather-by-name endpoint (this used to return a raw 404).
    Geocoding resolves it to a real lat/lon (e.g. the state's centroid),
    so weather now comes back live instead of erroring.
    """
    token = _register_and_login(client, email="telangana@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    monkeypatch.setattr(settings, "WEATHER_API_KEY", "test-key")
    monkeypatch.setattr(
        "httpx.AsyncClient.get",
        _fake_get_factory(geo_result=[{"lat": 18.11, "lon": 79.02, "name": "Telangana"}]),
    )

    response = client.get("/api/weather", headers=headers, params={"location": "Telangana"})

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "live"
    assert data["temperature"] == 29.0
    # The response still echoes back exactly what the farmer typed, not
    # OpenWeather's resolved name — unchanged existing display behavior.
    assert data["location"] == "Telangana"


def test_weather_full_city_state_country_still_works(client, monkeypatch):
    """Regression check: the previously-working well-formed case is unaffected."""
    token = _register_and_login(client, email="hyderabad@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    monkeypatch.setattr(settings, "WEATHER_API_KEY", "test-key")
    monkeypatch.setattr(
        "httpx.AsyncClient.get",
        _fake_get_factory(geo_result=[{"lat": 17.38, "lon": 78.49, "name": "Hyderabad"}]),
    )

    response = client.get(
        "/api/weather",
        headers=headers,
        params={"location": "Hyderabad, Telangana, India"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "live"
    assert data["location"] == "Hyderabad, Telangana, India"


def test_weather_invalid_location_returns_friendly_message(client, monkeypatch):
    """An unresolvable location (typo, gibberish) gets a clear, actionable
    message instead of a raw OpenWeather error."""
    token = _register_and_login(client, email="invalidloc@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    monkeypatch.setattr(settings, "WEATHER_API_KEY", "test-key")
    monkeypatch.setattr("httpx.AsyncClient.get", _fake_get_factory(geo_result=[]))

    response = client.get("/api/weather", headers=headers, params={"location": "xyzzynotarealplace"})

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "unavailable"
    assert data["temperature"] is None
    assert "city or town" in data["message"].lower()
    # Never a raw status code / vendor error string.
    assert "HTTP" not in data["message"]
    assert "404" not in data["message"]


def test_weather_upstream_failure_after_successful_geocode(client, monkeypatch):
    """Geocoding succeeds but the weather endpoint itself fails (rate limit,
    outage, etc.) — must degrade gracefully, never surface the raw status."""
    token = _register_and_login(client, email="upstreamfail@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    monkeypatch.setattr(settings, "WEATHER_API_KEY", "test-key")
    monkeypatch.setattr(
        "httpx.AsyncClient.get",
        _fake_get_factory(
            geo_result=[{"lat": 17.38, "lon": 78.49, "name": "Hyderabad"}],
            weather_status=500,
        ),
    )

    response = client.get(
        "/api/weather",
        headers=headers,
        params={"location": "Hyderabad, Telangana, India"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["source"] == "unavailable"
    assert "HTTP" not in data["message"]
    assert "500" not in data["message"]


def test_weather_response_never_contains_api_key(client, monkeypatch):
    """The configured API key must never leak into the response body."""
    token = _register_and_login(client, email="nokeyleak@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    monkeypatch.setattr(settings, "WEATHER_API_KEY", "super-secret-test-key")
    monkeypatch.setattr(
        "httpx.AsyncClient.get",
        _fake_get_factory(geo_result=[{"lat": 17.38, "lon": 78.49, "name": "Hyderabad"}]),
    )

    response = client.get(
        "/api/weather",
        headers=headers,
        params={"location": "Hyderabad, Telangana, India"},
    )

    assert response.status_code == 200
    assert "super-secret-test-key" not in response.text