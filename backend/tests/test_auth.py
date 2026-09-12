def test_register_new_user(client):
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test Farmer",
            "email": "farmer1@example.com",
            "password": "SecurePass123",
            "preferred_language": "en",
            "location": "Warangal, Telangana, India",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "farmer1@example.com"
    assert "password" not in data
    assert "password_hash" not in data


def test_register_duplicate_email_rejected(client):
    payload = {
        "name": "Dup User",
        "email": "dup@example.com",
        "password": "SecurePass123",
    }
    first = client.post("/api/auth/register", json=payload)
    assert first.status_code == 201
    second = client.post("/api/auth/register", json=payload)
    assert second.status_code == 409


def test_login_success_and_failure(client):
    client.post(
        "/api/auth/register",
        json={"name": "Login User", "email": "login@example.com", "password": "SecurePass123"},
    )
    ok = client.post("/api/auth/login", json={"email": "login@example.com", "password": "SecurePass123"})
    assert ok.status_code == 200
    assert "access_token" in ok.json()

    bad = client.post("/api/auth/login", json={"email": "login@example.com", "password": "WrongPass"})
    assert bad.status_code == 401


def test_me_requires_auth_token(client):
    unauthenticated = client.get("/api/auth/me")
    assert unauthenticated.status_code == 401

    client.post(
        "/api/auth/register",
        json={"name": "Me User", "email": "meuser@example.com", "password": "SecurePass123"},
    )
    login = client.post("/api/auth/login", json={"email": "meuser@example.com", "password": "SecurePass123"})
    token = login.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "meuser@example.com"


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
