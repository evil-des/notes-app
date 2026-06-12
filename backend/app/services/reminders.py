import re
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session, selectinload

from ..integrations.telegram import TelegramClient
from ..models import Note, NoteReminder, User

PENDING = "pending"
SENDING = "sending"
SENT = "sent"
FAILED = "failed"
MAX_ATTEMPTS = 5
DEFAULT_REMINDER_TIME = "09:00"
SUPPORTED_LANGUAGES = {"en", "ru"}
_REMINDER_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def validate_timezone(value: str) -> str:
    timezone = value.strip() or "UTC"
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("Invalid timezone") from exc
    return timezone


def validate_reminder_time(value: str) -> str:
    reminder_time = value.strip()
    if not _REMINDER_TIME_RE.fullmatch(reminder_time):
        raise ValueError("Invalid reminder time")
    return reminder_time


def validate_language(value: str) -> str:
    language = value.strip().lower()
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError("Invalid language")
    return language


def reminder_message(note: Note, language: str) -> str:
    if language == "ru":
        return f"Напоминание: {note.title}\nДата: {note.note_date.isoformat()}"
    return f"Reminder: {note.title}\nDate: {note.note_date.isoformat()}"


def scheduled_for_note_date(
    note_date: date,
    timezone: str,
    reminder_time: str = DEFAULT_REMINDER_TIME,
) -> datetime:
    reminder_clock = time.fromisoformat(validate_reminder_time(reminder_time))
    local_time = datetime.combine(note_date, reminder_clock, ZoneInfo(timezone))
    return local_time.astimezone(UTC)


def sync_note_reminder(db: Session, note: Note, user: User) -> None:
    if note.note_date is None:
        db.query(NoteReminder).filter(
            NoteReminder.note_id == note.id,
            NoteReminder.status.in_([PENDING, FAILED]),
        ).delete(synchronize_session=False)
        return

    db.query(NoteReminder).filter(
        NoteReminder.note_id == note.id,
        NoteReminder.status.in_([PENDING, FAILED]),
    ).delete(synchronize_session=False)

    sent_for_date = (
        db.query(NoteReminder)
        .filter(
            NoteReminder.note_id == note.id,
            NoteReminder.note_date == note.note_date,
            NoteReminder.status == SENT,
        )
        .first()
    )
    if sent_for_date is not None:
        return

    if note.archived_at is not None:
        return

    scheduled_for = scheduled_for_note_date(
        note.note_date,
        user.timezone or "UTC",
        user.reminder_time or DEFAULT_REMINDER_TIME,
    )
    existing = (
        db.query(NoteReminder)
        .filter(
            NoteReminder.note_id == note.id,
            NoteReminder.scheduled_for == scheduled_for,
        )
        .one_or_none()
    )
    if existing is None:
        db.add(
            NoteReminder(
                note_id=note.id,
                user_id=user.id,
                note_date=note.note_date,
                scheduled_for=scheduled_for,
                status=PENDING,
                attempts=0,
            )
        )


def resync_user_reminders(db: Session, user: User) -> None:
    notes = (
        db.query(Note)
        .filter(
            Note.user_id == user.id,
            Note.archived_at.is_(None),
            Note.note_date.is_not(None),
        )
        .all()
    )
    for note in notes:
        sync_note_reminder(db, note, user)


def _due_query(db: Session, now: datetime):
    return (
        db.query(NoteReminder)
        .options(selectinload(NoteReminder.note), selectinload(NoteReminder.user))
        .filter(
            NoteReminder.scheduled_for <= now,
            NoteReminder.attempts < MAX_ATTEMPTS,
            or_(
                NoteReminder.status == PENDING,
                and_(NoteReminder.status == FAILED, NoteReminder.sent_at.is_(None)),
            ),
        )
        .order_by(NoteReminder.scheduled_for.asc(), NoteReminder.id.asc())
    )


def send_due_reminders(
    db: Session,
    telegram: TelegramClient,
    now: datetime | None = None,
    limit: int = 50,
) -> int:
    now = now or datetime.now(UTC)
    query = _due_query(db, now)
    if db.bind is not None and db.bind.dialect.name == "postgresql":
        query = query.with_for_update(skip_locked=True, of=NoteReminder)
    reminders = query.limit(limit).all()

    sent = 0
    for reminder in reminders:
        note = reminder.note
        user = reminder.user
        if (
            note is None
            or user is None
            or note.archived_at is not None
            or not user.telegram_notifications_enabled
            or not user.telegram_chat_id
        ):
            continue

        reminder.status = SENDING
        db.flush()
        try:
            telegram.send_message(
                user.telegram_chat_id,
                reminder_message(note, user.language),
            )
        except Exception as exc:
            reminder.status = FAILED
            reminder.attempts += 1
            reminder.last_error = str(exc)[:1000]
        else:
            reminder.status = SENT
            reminder.sent_at = now
            reminder.last_error = None
            sent += 1
    db.commit()
    return sent
