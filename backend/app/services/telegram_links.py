import secrets
from typing import Any

from sqlalchemy.orm import Session

from ..config import settings
from ..models import IntegrationState, User

TELEGRAM_OFFSET_STATE = "telegram_update_offset"


def build_connect_url(token: str) -> str | None:
    username = settings.telegram_bot_username.strip().lstrip("@")
    if not username:
        return None
    return f"https://t.me/{username}?start={token}"


def ensure_link_token(db: Session, user: User) -> str:
    if user.telegram_link_token:
        return user.telegram_link_token
    while True:
        token = secrets.token_urlsafe(24)
        exists = db.query(User).filter(User.telegram_link_token == token).first()
        if exists is None:
            user.telegram_link_token = token
            db.flush()
            return token


def bind_chat_by_start_token(db: Session, token: str, chat_id: str) -> User | None:
    user = db.query(User).filter(User.telegram_link_token == token).one_or_none()
    if user is None:
        return None
    user.telegram_chat_id = str(chat_id)
    return user


def get_update_offset(db: Session) -> int | None:
    state = db.get(IntegrationState, TELEGRAM_OFFSET_STATE)
    if state is None or not state.value:
        return None
    return int(state.value)


def set_update_offset(db: Session, offset: int) -> None:
    state = db.get(IntegrationState, TELEGRAM_OFFSET_STATE)
    if state is None:
        db.add(IntegrationState(name=TELEGRAM_OFFSET_STATE, value=str(offset)))
    else:
        state.value = str(offset)


def handle_update(db: Session, update: dict[str, Any]) -> User | None:
    message = update.get("message") or {}
    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if chat_id is None or not text.startswith("/start"):
        return None
    parts = text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        return None
    return bind_chat_by_start_token(db, parts[1].strip(), str(chat_id))
