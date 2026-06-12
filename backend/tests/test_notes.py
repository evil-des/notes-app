def _auth(client, username="user1", password="pw123456"):
    client.post("/api/auth/register", json={"username": username, "password": password})
    r = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_create_and_list_note(client):
    h = _auth(client)
    r = client.post(
        "/api/notes",
        headers=h,
        json={"title": "T1", "content": "hello", "tags": ["Work", "work", " "]},
    )
    assert r.status_code == 201
    note = r.json()
    assert note["title"] == "T1"
    assert note["tags"] == ["work"]

    r = client.get("/api/notes", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_note_isolation_between_users(client):
    h1 = _auth(client, "alice", "pw123456")
    h2 = _auth(client, "eve", "pw123456")
    r = client.post("/api/notes", headers=h1, json={"title": "alice-note", "content": ""})
    nid = r.json()["id"]

    assert client.get(f"/api/notes/{nid}", headers=h2).status_code == 404
    assert client.get("/api/notes", headers=h2).json()["items"] == []


def test_owner_can_share_note_and_public_read_without_auth(client):
    h = _auth(client)
    r = client.post(
        "/api/notes",
        headers=h,
        json={
            "title": "public note",
            "content": "hello **world**",
            "tags": ["shared"],
            "note_date": "2026-06-13",
        },
    )
    nid = r.json()["id"]

    share = client.post(f"/api/notes/{nid}/share", headers=h)
    assert share.status_code == 200
    body = share.json()
    assert body["share_token"]
    assert body["shared_at"]

    public = client.get(f"/api/shared-notes/{body['share_token']}")
    assert public.status_code == 200
    public_body = public.json()
    assert public_body == {
        "title": "public note",
        "content": "hello **world**",
        "tags": ["shared"],
        "note_date": "2026-06-13",
        "created_at": public_body["created_at"],
        "updated_at": public_body["updated_at"],
    }
    assert "user_id" not in public_body
    assert "share_token" not in public_body
    assert "shared_at" not in public_body
    assert "archived_at" not in public_body
    assert "pinned_at" not in public_body


def test_share_note_is_idempotent(client):
    h = _auth(client)
    r = client.post("/api/notes", headers=h, json={"title": "n1", "content": ""})
    nid = r.json()["id"]

    first = client.post(f"/api/notes/{nid}/share", headers=h).json()
    second = client.post(f"/api/notes/{nid}/share", headers=h).json()

    assert second["share_token"] == first["share_token"]
    assert second["shared_at"] == first["shared_at"]


def test_other_user_cannot_share_or_unshare_note(client):
    h1 = _auth(client, "alice", "pw123456")
    h2 = _auth(client, "eve", "pw123456")
    r = client.post("/api/notes", headers=h1, json={"title": "alice-note", "content": ""})
    nid = r.json()["id"]

    assert client.post(f"/api/notes/{nid}/share", headers=h2).status_code == 404
    shared = client.post(f"/api/notes/{nid}/share", headers=h1).json()
    assert client.delete(f"/api/notes/{nid}/share", headers=h2).status_code == 404
    assert client.get(f"/api/shared-notes/{shared['share_token']}").status_code == 200


def test_unshare_revokes_public_access(client):
    h = _auth(client)
    r = client.post("/api/notes", headers=h, json={"title": "n1", "content": ""})
    nid = r.json()["id"]
    token = client.post(f"/api/notes/{nid}/share", headers=h).json()["share_token"]

    unshare = client.delete(f"/api/notes/{nid}/share", headers=h)
    assert unshare.status_code == 200
    assert unshare.json()["share_token"] is None
    assert unshare.json()["shared_at"] is None
    assert client.get(f"/api/shared-notes/{token}").status_code == 404


def test_unknown_shared_note_token_returns_404(client):
    assert client.get("/api/shared-notes/not-a-real-token").status_code == 404


def test_search_notes(client):
    h = _auth(client)
    client.post("/api/notes", headers=h, json={"title": "Go shopping", "content": ""})
    client.post("/api/notes", headers=h, json={"title": "Read book", "content": "about Go"})
    r = client.get("/api/notes", headers=h, params={"q": "go"})
    assert r.status_code == 200
    assert r.json()["total"] == 2


def test_calendar_excludes_archived(client):
    h = _auth(client)
    r1 = client.post(
        "/api/notes",
        headers=h,
        json={"title": "dated", "content": "", "note_date": "2026-04-10"},
    )
    client.post("/api/notes", headers=h, json={"title": "undated", "content": ""})
    # Archive the dated one — calendar should then be empty for the month.
    nid = r1.json()["id"]
    assert client.post(f"/api/notes/{nid}/archive", headers=h).status_code == 200

    r = client.get("/api/notes/calendar", headers=h, params={"year": 2026, "month": 4})
    assert r.status_code == 200
    assert r.json() == []


def test_calendar(client):
    h = _auth(client)
    client.post(
        "/api/notes",
        headers=h,
        json={"title": "dated", "content": "", "note_date": "2026-04-10"},
    )
    r = client.get("/api/notes/calendar", headers=h, params={"year": 2026, "month": 4})
    days = r.json()
    assert len(days) == 1
    assert days[0]["date"] == "2026-04-10"


def test_tags_endpoint(client):
    h = _auth(client)
    client.post(
        "/api/notes", headers=h, json={"title": "n1", "content": "", "tags": ["work", "urgent"]}
    )
    client.post("/api/notes", headers=h, json={"title": "n2", "content": "", "tags": ["personal"]})
    r = client.get("/api/tags", headers=h)
    assert sorted(r.json()) == ["personal", "urgent", "work"]


def test_filter_by_tag(client):
    h = _auth(client)
    client.post("/api/notes", headers=h, json={"title": "n1", "content": "", "tags": ["work"]})
    client.post("/api/notes", headers=h, json={"title": "n2", "content": "", "tags": ["home"]})
    r = client.get("/api/notes", headers=h, params={"tag": "work"})
    items = r.json()["items"]
    assert [n["title"] for n in items] == ["n1"]
