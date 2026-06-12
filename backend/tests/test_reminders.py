from datetime import UTC, datetime

from app.models import NoteReminder, User
from app.services.reminders import (
    FAILED,
    PENDING,
    SENT,
    scheduled_for_note_date,
    send_due_reminders,
)
from app.services.telegram_links import bind_chat_by_start_token, ensure_link_token, handle_update


def _auth(client, username="user1", password="pw123456"):
    client.post("/api/auth/register", json={"username": username, "password": password})
    r = client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


class FakeTelegram:
    def __init__(self, fail=False):
        self.fail = fail
        self.messages = []

    def send_message(self, chat_id, text):
        if self.fail:
            raise RuntimeError("telegram unavailable")
        self.messages.append((chat_id, text))


def test_scheduled_for_uses_user_timezone():
    scheduled = scheduled_for_note_date(datetime(2026, 6, 12).date(), "Europe/Moscow")
    assert scheduled == datetime(2026, 6, 12, 6, 0, tzinfo=UTC)


def test_scheduled_for_uses_custom_reminder_time():
    scheduled = scheduled_for_note_date(
        datetime(2026, 6, 12).date(),
        "Europe/Moscow",
        "18:45",
    )
    assert scheduled == datetime(2026, 6, 12, 15, 45, tzinfo=UTC)


def test_note_create_update_and_archive_sync_reminders(client):
    h = _auth(client)

    r = client.patch("/api/account/settings", headers=h, json={"timezone": "Europe/Moscow"})
    assert r.status_code == 200
    r = client.post(
        "/api/notes",
        headers=h,
        json={"title": "dated", "content": "", "note_date": "2026-06-12"},
    )
    note_id = r.json()["id"]

    db = client.db_sessionmaker()
    try:
        reminders = db.query(NoteReminder).filter(NoteReminder.note_id == note_id).all()
        assert len(reminders) == 1
        assert reminders[0].status == PENDING
        assert reminders[0].scheduled_for.replace(tzinfo=UTC) == datetime(
            2026, 6, 12, 6, 0, tzinfo=UTC
        )
    finally:
        db.close()

    r = client.put(
        f"/api/notes/{note_id}",
        headers=h,
        json={"title": "dated", "content": "", "note_date": "2026-06-13"},
    )
    assert r.status_code == 200
    db = client.db_sessionmaker()
    try:
        reminders = db.query(NoteReminder).filter(NoteReminder.note_id == note_id).all()
        assert len(reminders) == 1
        assert reminders[0].scheduled_for.replace(tzinfo=UTC) == datetime(
            2026, 6, 13, 6, 0, tzinfo=UTC
        )
    finally:
        db.close()


def test_settings_time_change_resyncs_pending_reminders(client):
    h = _auth(client)
    client.patch("/api/account/settings", headers=h, json={"timezone": "Europe/Moscow"})
    r = client.post(
        "/api/notes",
        headers=h,
        json={"title": "dated", "content": "", "note_date": "2026-06-12"},
    )
    note_id = r.json()["id"]

    r = client.patch("/api/account/settings", headers=h, json={"reminder_time": "18:45"})
    assert r.status_code == 200

    db = client.db_sessionmaker()
    try:
        reminders = db.query(NoteReminder).filter(NoteReminder.note_id == note_id).all()
        assert len(reminders) == 1
        assert reminders[0].scheduled_for.replace(tzinfo=UTC) == datetime(
            2026, 6, 12, 15, 45, tzinfo=UTC
        )
    finally:
        db.close()

    assert client.post(f"/api/notes/{note_id}/archive", headers=h).status_code == 200
    db = client.db_sessionmaker()
    try:
        reminders = db.query(NoteReminder).filter(NoteReminder.note_id == note_id).all()
        assert reminders == []
    finally:
        db.close()


def test_send_due_reminder_once(client):
    h = _auth(client)
    client.post(
        "/api/notes",
        headers=h,
        json={"title": "today", "content": "", "note_date": "2026-06-12"},
    )

    db = client.db_sessionmaker()
    try:
        user = db.query(User).one()
        token = ensure_link_token(db, user)
        assert bind_chat_by_start_token(db, token, "12345") == user
        user.telegram_notifications_enabled = True
        user.language = "ru"
        db.commit()

        telegram = FakeTelegram()
        now = datetime(2026, 6, 12, 10, 0, tzinfo=UTC)
        assert send_due_reminders(db, telegram, now=now) == 1
        assert send_due_reminders(db, telegram, now=now) == 0
        assert len(telegram.messages) == 1
        assert telegram.messages[0][1].startswith("Напоминание: today")
        assert db.query(NoteReminder).one().status == SENT
    finally:
        db.close()


def test_send_due_reminder_records_failure_for_retry(client):
    h = _auth(client)
    client.post(
        "/api/notes",
        headers=h,
        json={"title": "today", "content": "", "note_date": "2026-06-12"},
    )

    db = client.db_sessionmaker()
    try:
        user = db.query(User).one()
        token = ensure_link_token(db, user)
        bind_chat_by_start_token(db, token, "12345")
        user.telegram_notifications_enabled = True
        db.commit()

        now = datetime(2026, 6, 12, 10, 0, tzinfo=UTC)
        assert send_due_reminders(db, FakeTelegram(fail=True), now=now) == 0
        reminder = db.query(NoteReminder).one()
        assert reminder.status == FAILED
        assert reminder.attempts == 1
        assert "telegram unavailable" in reminder.last_error
    finally:
        db.close()


def test_handle_start_update_binds_chat(client):
    db = client.db_sessionmaker()
    try:
        user = User(username="alice", password_hash="x")
        db.add(user)
        db.flush()
        token = ensure_link_token(db, user)
        update = {"message": {"text": f"/start {token}", "chat": {"id": 777}}}
        assert handle_update(db, update) == user
        assert user.telegram_chat_id == "777"
    finally:
        db.close()
