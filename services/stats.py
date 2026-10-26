"""Статистика натискань — зберігається у data/stats.json."""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("bot.stats")

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_STATS_FILE = _DATA_DIR / "stats.json"

button_clicks: dict[str, int] = defaultdict(int)
unique_users: set[int] = set()
start_time = datetime.now()


def _load() -> None:
    global button_clicks, unique_users
    try:
        if not _STATS_FILE.exists():
            return
        raw = json.loads(_STATS_FILE.read_text(encoding="utf-8"))
        button_clicks = defaultdict(int, {str(k): int(v) for k, v in (raw.get("clicks") or {}).items()})
        unique_users = {int(x) for x in (raw.get("users") or [])}
        logger.info("stats loaded: users=%s clicks=%s", len(unique_users), sum(button_clicks.values()))
    except Exception as e:
        logger.warning("stats load failed: %s", e)


def _save() -> None:
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        payload = {
            "users": sorted(unique_users),
            "clicks": dict(button_clicks),
        }
        _STATS_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning("stats save failed: %s", e)


_load()


def log_button(user_id: int, button: str) -> None:
    unique_users.add(user_id)
    button_clicks[button] += 1
    total = sum(button_clicks.values())
    if total % 20 == 0:
        _save()


def flush_stats() -> None:
    _save()


def get_stats() -> str:
    uptime = datetime.now() - start_time
    hours, remainder = divmod(int(uptime.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)

    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Унікальних користувачів: <b>{len(unique_users)}</b>\n"
        f"⏱ Час роботи (сесія): <b>{hours}г {minutes}хв {seconds}с</b>\n\n"
        f"<b>Топ натискань:</b>\n"
    )

    sorted_buttons = sorted(button_clicks.items(), key=lambda x: x[1], reverse=True)[:15]
    if not sorted_buttons:
        text += "Поки порожньо"
    else:
        for btn, count in sorted_buttons:
            text += f"• <code>{btn}</code> — <b>{count}</b>\n"
    return text
