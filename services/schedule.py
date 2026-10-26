"""Приблизний розклад метро Харкова (Europe/Kyiv). Тексти — з locales."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from locales import t

KYIV = ZoneInfo("Europe/Kyiv")

INTERVALS = [
    (5, 30, 7, 0, 10),
    (7, 0, 9, 15, 5),
    (9, 15, 15, 30, 10),
    (15, 30, 19, 0, 5),
    (19, 0, 20, 0, 10),
    (20, 0, 22, 0, 15),
]

WORK_START = (5, 30)
WORK_END = (22, 0)


def _now(now: datetime | None = None) -> datetime:
    if now is None:
        return datetime.now(KYIV)
    if now.tzinfo is None:
        return now.replace(tzinfo=KYIV)
    return now.astimezone(KYIV)


def _minutes(h: int, m: int) -> int:
    return h * 60 + m


def get_interval(now: datetime | None = None) -> int | None:
    now = _now(now)
    cur = _minutes(now.hour, now.minute)
    if cur < _minutes(*WORK_START) or cur >= _minutes(*WORK_END):
        return None
    for sh, sm, eh, em, interval in INTERVALS:
        if _minutes(sh, sm) <= cur < _minutes(eh, em):
            return interval
    return 15


def next_trains(count: int = 6, now: datetime | None = None) -> list[str]:
    now = _now(now)
    if get_interval(now) is None:
        return []
    base = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
    times: list[str] = []
    t_cur = base
    for _ in range(count * 3):
        iv = get_interval(t_cur)
        if iv is None:
            break
        times.append(t_cur.strftime("%H:%M"))
        t_cur += timedelta(minutes=iv)
        if len(times) >= count:
            break
    return times


def format_schedule(lang: str = "uk") -> str:
    now = _now()
    trains = next_trains(6, now)
    interval = get_interval(now)
    if not trains:
        return t(lang, "schedule_closed")
    return t(lang, "schedule_open", interval=interval, times=", ".join(trains))
