def _register_login(client, username="user1", password="pw123456"):
    client.post("/api/auth/register", json={"username": username, "password": password})
    r = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_change_password(client):
    h = _register_login(client)

    # Wrong old password.
    r = client.post(
        "/api/account/change-password",
        headers=h,
        json={"current_password": "wrong", "new_password": "newpass123"},
    )
    assert r.status_code == 401

    # Correct old password.
    r = client.post(
        "/api/account/change-password",
        headers=h,
        json={"current_password": "pw123456", "new_password": "newpass123"},
    )
    assert r.status_code == 200

    # Old password no longer works.
    r = client.post("/api/auth/login", data={"username": "user1", "password": "pw123456"})
    assert r.status_code == 401

    # New password works.
    r = client.post("/api/auth/login", data={"username": "user1", "password": "newpass123"})
    assert r.status_code == 200


def test_change_password_wrong_current_password_is_rate_limited(client):
    h = _register_login(client)

    for _ in range(5):
        r = client.post(
            "/api/account/change-password",
            headers=h,
            json={"current_password": "wrong", "new_password": "newpass123"},
        )
        assert r.status_code == 401

    r = client.post(
        "/api/account/change-password",
        headers=h,
        json={"current_password": "wrong", "new_password": "newpass123"},
    )
    assert r.status_code == 429


def test_delete_account(client):
    h = _register_login(client, "alice", "pw123456")
    client.post("/api/notes", headers=h, json={"title": "mine", "content": ""})

    # Wrong password.
    r = client.request(
        "DELETE",
        "/api/account",
        headers=h,
        json={"password": "wrong"},
    )
    assert r.status_code == 401

    # Correct password.
    r = client.request(
        "DELETE",
        "/api/account",
        headers=h,
        json={"password": "pw123456"},
    )
    assert r.status_code == 204

    # Subsequent requests with the old token should fail (user gone).
    r = client.get("/api/notes", headers=h)
    assert r.status_code == 401

    # Username can now be taken by a new registration.
    r = client.post("/api/auth/register", json={"username": "alice", "password": "newpass123"})
    assert r.status_code == 201


def test_get_and_update_notification_settings(client):
    h = _register_login(client)

    r = client.get("/api/account/settings", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["telegram_connected"] is False
    assert body["telegram_notifications_enabled"] is False
    assert body["timezone"] == "UTC"
    assert body["reminder_time"] == "09:00"
    assert body["language"] == "en"
    assert "telegram_connect_url" in body

    r = client.patch(
        "/api/account/settings",
        headers=h,
        json={"timezone": "Europe/Moscow", "reminder_time": "10:30", "language": "ru"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["timezone"] == "Europe/Moscow"
    assert body["reminder_time"] == "10:30"
    assert body["language"] == "ru"

    r = client.patch("/api/account/settings", headers=h, json={"timezone": "No/SuchZone"})
    assert r.status_code == 422

    r = client.patch("/api/account/settings", headers=h, json={"reminder_time": "24:00"})
    assert r.status_code == 422

    r = client.patch("/api/account/settings", headers=h, json={"language": "fr"})
    assert r.status_code == 422


def test_cannot_enable_telegram_notifications_before_connecting(client):
    h = _register_login(client)

    r = client.patch(
        "/api/account/settings",
        headers=h,
        json={"telegram_notifications_enabled": True},
    )
    assert r.status_code == 400


def test_create_telegram_link(client):
    h = _register_login(client)

    r = client.post("/api/account/telegram/link", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body["telegram_bot_configured"], bool)
    assert body["telegram_connect_url"] is None or body["telegram_connect_url"].startswith(
        "https://t.me/"
    )
