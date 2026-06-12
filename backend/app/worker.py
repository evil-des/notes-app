import logging
import time

from apscheduler.schedulers.background import BackgroundScheduler

from .config import settings
from .db import SessionLocal
from .integrations.telegram import TelegramClient
from .services.reminders import send_due_reminders
from .services.telegram_links import get_update_offset, handle_update, set_update_offset

logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def process_due_reminders() -> None:
    db = SessionLocal()
    try:
        sent = send_due_reminders(db, TelegramClient(settings.telegram_bot_token))
        if sent:
            logger.info("Sent %s note reminder(s).", sent)
    finally:
        db.close()


def process_telegram_updates() -> None:
    telegram = TelegramClient(settings.telegram_bot_token)
    if not telegram.enabled:
        logger.info("Telegram token is not configured; update polling is disabled.")
        return

    db = SessionLocal()
    try:
        offset = get_update_offset(db)
        updates = telegram.get_updates(offset=offset, timeout=0)
        for update in updates:
            update_id = update.get("update_id")
            if isinstance(update_id, int):
                set_update_offset(db, update_id + 1)
            user = handle_update(db, update)
            if user is not None:
                telegram.send_message(
                    user.telegram_chat_id or "",
                    "Telegram connected. You can enable note reminders in Settings.",
                )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to process Telegram updates.")
    finally:
        db.close()


def main() -> None:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(
        process_due_reminders,
        "interval",
        seconds=settings.reminder_worker_interval_seconds,
        max_instances=1,
        id="due-reminders",
    )
    scheduler.add_job(
        process_telegram_updates,
        "interval",
        seconds=settings.telegram_updates_interval_seconds,
        max_instances=1,
        id="telegram-updates",
    )
    scheduler.start()
    logger.info("Reminder worker started.")
    try:
        while True:
            time.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()
