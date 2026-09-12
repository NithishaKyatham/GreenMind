def _register_and_login(client, email="chat@example.com"):
    client.post("/api/auth/register", json={"name": "Chat User", "email": email, "password": "SecurePass123"})
    login = client.post("/api/auth/login", json={"email": email, "password": "SecurePass123"})
    return login.json()["access_token"]


def test_chatbot_rule_based_fallback(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/chatbot/message",
        headers=headers,
        json={"message": "My tomato leaves have yellow spots"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "rule_based_fallback"  # no AI_API_KEY set in tests
    assert data["reply"]
    assert data["conversation_id"]

    # Follow-up in same conversation retains context/thread
    follow_up = client.post(
        "/api/chatbot/message",
        headers=headers,
        json={"message": "There are brown patches too", "conversation_id": data["conversation_id"]},
    )
    assert follow_up.status_code == 200
    assert follow_up.json()["conversation_id"] == data["conversation_id"]
