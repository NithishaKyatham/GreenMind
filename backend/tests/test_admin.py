def test_admin_endpoints_require_admin(client):
    client.post("/api/auth/register", json={"name": "Regular", "email": "regular@example.com", "password": "SecurePass123"})
    login = client.post("/api/auth/login", json={"email": "regular@example.com", "password": "SecurePass123"})
    token = login.json()["access_token"]

    response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
