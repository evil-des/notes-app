from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..auth import hash_password, verify_password
from ..config import settings
from ..deps import get_current_user, get_db
from ..models import User
from ..rate_limit import (
    auth_rate_limit_key,
    check_auth_rate_limit,
    clear_auth_failures,
    record_auth_failure,
)
from ..schemas import (
    AccountSettingsOut,
    AccountSettingsUpdate,
    ChangePasswordIn,
    DeleteAccountIn,
    OkOut,
    TelegramLinkOut,
)
from ..services.reminders import (
    resync_user_reminders,
    validate_language,
    validate_reminder_time,
    validate_timezone,
)
from ..services.telegram_links import build_connect_url, ensure_link_token

router = APIRouter(prefix="/account", tags=["account"])


def _settings_out(db: Session, user: User) -> AccountSettingsOut:
    token = ensure_link_token(db, user)
    db.flush()
    return AccountSettingsOut(
        telegram_connected=bool(user.telegram_chat_id),
        telegram_notifications_enabled=user.telegram_notifications_enabled,
        timezone=user.timezone,
        reminder_time=user.reminder_time,
        language=user.language,
        telegram_bot_configured=bool(settings.telegram_bot_token.strip()),
        telegram_connect_url=build_connect_url(token),
    )


@router.get("/settings", response_model=AccountSettingsOut)
def get_settings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountSettingsOut:
    payload = _settings_out(db, user)
    db.commit()
    return payload


@router.patch("/settings", response_model=AccountSettingsOut)
def update_settings(
    payload: AccountSettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccountSettingsOut:
    should_resync_reminders = False
    if payload.timezone is not None:
        try:
            user.timezone = validate_timezone(payload.timezone)
        except ValueError:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid timezone") from None
        should_resync_reminders = True
    if payload.reminder_time is not None:
        try:
            user.reminder_time = validate_reminder_time(payload.reminder_time)
        except ValueError:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid reminder time"
            ) from None
        should_resync_reminders = True
    if payload.telegram_notifications_enabled is not None:
        if payload.telegram_notifications_enabled and not user.telegram_chat_id:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Connect Telegram first")
        user.telegram_notifications_enabled = payload.telegram_notifications_enabled
    if payload.language is not None:
        try:
            user.language = validate_language(payload.language)
        except ValueError:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Invalid language") from None
    if should_resync_reminders:
        resync_user_reminders(db, user)
    response = _settings_out(db, user)
    db.commit()
    return response


@router.post("/telegram/link", response_model=TelegramLinkOut)
def create_telegram_link(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TelegramLinkOut:
    token = ensure_link_token(db, user)
    db.commit()
    return TelegramLinkOut(
        telegram_connect_url=build_connect_url(token),
        telegram_bot_configured=bool(settings.telegram_bot_token.strip()),
    )


@router.post("/change-password", response_model=OkOut)
def change_password(
    request: Request,
    payload: ChangePasswordIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OkOut:
    rate_limit_key = auth_rate_limit_key(request, "change-password", user.id)
    check_auth_rate_limit(rate_limit_key)
    if not verify_password(payload.current_password, user.password_hash):
        record_auth_failure(rate_limit_key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Current password is wrong")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    clear_auth_failures(rate_limit_key)
    return OkOut()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    request: Request,
    payload: DeleteAccountIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    rate_limit_key = auth_rate_limit_key(request, "delete-account", user.id)
    check_auth_rate_limit(rate_limit_key)
    if not verify_password(payload.password, user.password_hash):
        record_auth_failure(rate_limit_key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Password is wrong")
    db.delete(user)
    db.commit()
    clear_auth_failures(rate_limit_key)
