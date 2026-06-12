import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class TelegramClient:
    def __init__(self, token: str, timeout: float = 10.0):
        self.token = token.strip()
        self.timeout = timeout

    @property
    def enabled(self) -> bool:
        return bool(self.token)

    def _url(self, method: str) -> str:
        return f"https://api.telegram.org/bot{self.token}/{method}"

    def get_updates(self, offset: int | None = None, timeout: int = 0) -> list[dict[str, Any]]:
        if not self.enabled:
            logger.info("Telegram token is not configured; skipping getUpdates.")
            return []
        params: dict[str, int] = {"timeout": timeout}
        if offset is not None:
            params["offset"] = offset
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(self._url("getUpdates"), params=params)
            response.raise_for_status()
            payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(str(payload.get("description") or "Telegram getUpdates failed"))
        return payload.get("result", [])

    def send_message(self, chat_id: str, text: str) -> None:
        if not self.enabled:
            logger.info("Telegram token is not configured; skipping sendMessage.")
            return
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                self._url("sendMessage"),
                json={"chat_id": chat_id, "text": text},
            )
            response.raise_for_status()
            payload = response.json()
        if not payload.get("ok"):
            raise RuntimeError(str(payload.get("description") or "Telegram sendMessage failed"))
