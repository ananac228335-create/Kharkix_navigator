import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject

logger = logging.getLogger("bot")


def _user_label(user) -> str:
    """Нік + @username + id."""
    if not user:
        return "?"
    name = (user.full_name or "").strip() or "—"
    uname = f"@{user.username}" if user.username else "—"
    return f"{name} ({uname}, id={user.id})"


class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = None
        action = None

        if isinstance(event, Message):
            user = event.from_user
            action = f"msg:{event.text!r}" if event.text else "msg"
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            action = f"cb:{event.data!r}"

        if user and action:
            logger.info("%s | %s", _user_label(user), action)

        return await handler(event, data)
