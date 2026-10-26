"""
Система сповіщень про повітряну тривогу.

Джерело: https://alerts.com.ua/api/states
Регіон підписки: Харківська область (id=19)

Також вміє показати: тривога є в інших областях, але НЕ в Харкові —
з текстом і простою схемою-картинкою.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Set

import aiohttp
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.types import BufferedInputFile

from locales import t, region_name, get_user_lang as _locale_get_user_lang

logger = logging.getLogger("bot.alerts")

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_SUBSCRIBERS_FILE = _DATA_DIR / "alert_subscribers.json"

subscribed_users: Set[int] = set()

last_alert_state: dict[str, Any] = {
    "kharkiv_oblast": False,
    "active_ids": [],
}

_first_check_done: bool = False

KHARKIV_OBLAST_ID = 19
API_URL = "https://alerts.com.ua/api/states"
CHECK_INTERVAL_SEC = 30


def _load_subscribers() -> None:
    global subscribed_users
    try:
        if _SUBSCRIBERS_FILE.exists():
            raw = json.loads(_SUBSCRIBERS_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                subscribed_users = {int(x) for x in raw}
                logger.info("loaded %s alert subscribers from file", len(subscribed_users))
            else:
                subscribed_users = set()
        else:
            subscribed_users = set()
    except Exception as e:
        logger.warning("failed to load subscribers: %s", e)
        subscribed_users = set()


def _save_subscribers_sync() -> None:
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        _SUBSCRIBERS_FILE.write_text(
            json.dumps(sorted(subscribed_users), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning("failed to save subscribers: %s", e)


_load_subscribers()


async def check_alerts() -> dict[str, Any]:
    """
    Повертає:
      kharkiv_oblast: bool
      active_ids: list[int]  — id областей з активною тривогою
      states: list[dict]     — сирі записи API (id, name, alert)
    """
    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                API_URL,
                headers={"User-Agent": "DiscoverKharkivBot/1.3"},
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)

        active_ids: list[int] = []
        oblast_alert = False
        states = data.get("states") or []
        for state in states:
            sid = state.get("id")
            if state.get("alert") and sid is not None:
                active_ids.append(int(sid))
                if int(sid) == KHARKIV_OBLAST_ID:
                    oblast_alert = True

        logger.debug(
            "check_alerts: kharkiv=%s active=%s",
            oblast_alert,
            active_ids,
        )
        return {
            "kharkiv_oblast": oblast_alert,
            "active_ids": active_ids,
            "states": states,
        }
    except Exception as e:
        logger.warning("alerts API error: %s", e)
        return dict(last_alert_state)


def _get_user_lang(user_id: int) -> str:
    try:
        return _locale_get_user_lang(user_id)
    except Exception:
        return "uk"


def format_status_text(lang: str, state: dict[str, Any]) -> str:
    """Повний текст статусу (з урахуванням інших областей)."""
    kh = bool(state.get("kharkiv_oblast"))
    active_ids: list[int] = list(state.get("active_ids") or [])
    others = [i for i in active_ids if i != KHARKIV_OBLAST_ID]

    if kh:
        return t(lang, "alert_active")

    if others:
        lines = [t(lang, "alert_elsewhere_title")]
        # імена з API якщо є, інакше з REGION_NAMES
        name_by_id: dict[int, str] = {}
        for s in state.get("states") or []:
            if s.get("id") is not None:
                name_by_id[int(s["id"])] = str(s.get("name") or "")
        for rid in others:
            api_name = name_by_id.get(rid, "")
            name = region_name(lang, rid, api_name)
            lines.append(t(lang, "alert_regions_list_item", name=name))
        lines.append(t(lang, "alert_elsewhere_footer"))
        return "\n".join(lines)

    return t(lang, "alert_none_anywhere")


async def get_current_status_text(lang: str = "uk") -> str:
    state = await check_alerts()
    return format_status_text(lang, state)


async def get_status_payload(lang: str = "uk") -> dict[str, Any]:
    """
    Текст + кольорова картка рівня:
      red    — тривога в Харкові
      yellow — у Харкові тихо, але є в інших областях
      green  — ніде (або лише «все спокійно» в Харкові без інших)
    """
    state = await check_alerts()
    text_body = format_status_text(lang, state)
    kh = bool(state.get("kharkiv_oblast"))
    others = [i for i in (state.get("active_ids") or []) if i != KHARKIV_OBLAST_ID]
    if kh:
        level = "red"
    elif others:
        level = "yellow"
    else:
        level = "green"
    png: bytes | None = None
    try:
        from services.alert_map import build_level_card
        png = build_level_card(level, lang=lang)
    except Exception as e:
        logger.warning("alert map build failed: %s", e)
    return {"text": text_body, "png": png, "state": state, "level": level}


async def alerts_worker(bot: Bot) -> None:
    global last_alert_state, _first_check_done
    logger.info(
        "alerts worker started (interval=%ss, subscribers=%s)",
        CHECK_INTERVAL_SEC,
        len(subscribed_users),
    )

    while True:
        try:
            current = await check_alerts()
            was = last_alert_state.get("kharkiv_oblast", False)
            now = current.get("kharkiv_oblast", False)

            if _first_check_done:
                if now and not was:
                    logger.info("ALERT STARTED | subscribers=%s", len(subscribed_users))
                    await notify_users_by_lang(bot, start=True)
                elif not now and was:
                    logger.info("ALERT ENDED | subscribers=%s", len(subscribed_users))
                    await notify_users_by_lang(bot, start=False)
            else:
                logger.info(
                    "alerts first check: kharkiv_oblast=%s subscribers=%s",
                    now,
                    len(subscribed_users),
                )
                _first_check_done = True

            last_alert_state = current

        except Exception as e:
            logger.exception("alerts worker error: %s", e)

        await asyncio.sleep(CHECK_INTERVAL_SEC)


async def notify_users_by_lang(bot: Bot, start: bool) -> None:
    dead: list[int] = []
    for user_id in list(subscribed_users):
        try:
            lang = _get_user_lang(user_id)
            key = "alert_start" if start else "alert_end"
            await bot.send_message(user_id, t(lang, key), parse_mode=ParseMode.HTML)
            logger.info("alert sent to user_id=%s (start=%s)", user_id, start)
        except Exception as e:
            logger.warning("failed to notify user_id=%s: %s", user_id, e)
            dead.append(user_id)
    for uid in dead:
        subscribed_users.discard(uid)
    if dead:
        _save_subscribers_sync()


def subscribe(user_id: int) -> None:
    subscribed_users.add(user_id)
    _save_subscribers_sync()
    logger.info("subscribe user_id=%s total=%s", user_id, len(subscribed_users))


def unsubscribe(user_id: int) -> None:
    subscribed_users.discard(user_id)
    _save_subscribers_sync()
    logger.info("unsubscribe user_id=%s total=%s", user_id, len(subscribed_users))


def is_subscribed(user_id: int) -> bool:
    return user_id in subscribed_users


async def is_alert_active() -> bool:
    state = await check_alerts()
    return bool(state.get("kharkiv_oblast"))


async def send_current_status_if_active(bot: Bot, user_id: int) -> None:
    try:
        state = await check_alerts()
        if state.get("kharkiv_oblast"):
            lang = _get_user_lang(user_id)
            await bot.send_message(user_id, t(lang, "alert_start"), parse_mode=ParseMode.HTML)
            logger.info("sent current active alert to newly subscribed user_id=%s", user_id)
    except Exception as e:
        logger.warning("send_current_status_if_active failed for %s: %s", user_id, e)


async def send_status_to_user(bot: Bot, user_id: int, chat_id: int | None = None) -> None:
    """Надіслати актуальний статус (+ схему, якщо тривога не в Харкові)."""
    lang = _get_user_lang(user_id)
    payload = await get_status_payload(lang)
    target = chat_id or user_id
    text = payload["text"]
    png = payload.get("png")
    if png:
        caption = (text[:900] + "\n\n" + t(lang, "alert_map_caption"))[:1024]
        await bot.send_photo(
            target,
            photo=BufferedInputFile(png, filename="alert_scheme.png"),
            caption=caption,
            parse_mode=ParseMode.HTML,
        )
    else:
        await bot.send_message(target, text, parse_mode=ParseMode.HTML)
