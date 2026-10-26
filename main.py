import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

from config import BOT_TOKEN, ADMIN_IDS
from handlers.start import router as start_router
from handlers.metro import router as metro_router
from handlers.places import router as places_router
from handlers.extra import router as extra_router
from handlers.game import router as game_router
from middlewares.logging import LoggingMiddleware
from services.alerts import alerts_worker
from services.stats import flush_stats


class _ColorFormatter(logging.Formatter):
    """Компактні однорядкові логи з кольором рівня."""
    COLORS = {
        logging.DEBUG: "\033[90m",
        logging.INFO: "\033[32m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, "")
        time_str = self.formatTime(record, "%H:%M:%S")
        level = record.levelname[:4]
        msg = record.getMessage()
        name = record.name
        if name.startswith("bot"):
            name = "bot"
        line = f"{time_str} {level} {name} | {msg}"
        return f"{color}{line}{self.RESET}"


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_ColorFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)


PUBLIC_COMMANDS = [
    BotCommand(command="start", description="Старт / Start"),
    BotCommand(command="help", description="Допомога / Help"),
    BotCommand(command="alerts", description="Тривога / Alerts"),
    BotCommand(command="status", description="Статус тривоги зараз / Alert status"),
]

ADMIN_COMMANDS = PUBLIC_COMMANDS + [
    BotCommand(command="stats", description="Статистика (admin)"),
]


async def setup_commands(bot: Bot) -> None:
    """Публічні команди для всіх; /stats тільки для адмінів."""
    await bot.set_my_commands(PUBLIC_COMMANDS, scope=BotCommandScopeDefault())
    for admin_id in ADMIN_IDS:
        try:
            await bot.set_my_commands(
                ADMIN_COMMANDS,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except Exception as e:
            logging.getLogger("bot").warning(
                "cannot set admin commands for %s: %s", admin_id, e
            )


async def main() -> None:
    setup_logging()
    logger = logging.getLogger("bot")

    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("BOT_TOKEN не знайдено! Створи файл .env з рядком BOT_TOKEN=...")
        return

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())

    dp.include_router(start_router)
    dp.include_router(metro_router)
    dp.include_router(places_router)
    dp.include_router(extra_router)
    dp.include_router(game_router)

    asyncio.create_task(alerts_worker(bot))

    await setup_commands(bot)

    logger.info("Бот запущено")
    try:
        await dp.start_polling(bot)
    finally:
        flush_stats()
        logger.info("stats flushed on shutdown")


if __name__ == "__main__":
    asyncio.run(main())
