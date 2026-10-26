"""Кеш JSON-даних з диска (один раз на старті / при зміні mtime)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("bot.cache")

_ROOT = Path(__file__).resolve().parent.parent / "data"
_cache: dict[str, tuple[float, Any]] = {}


def load_json(name: str, default: Any = None) -> Any:
    """Завантажити JSON з data/<name>. Кешує за mtime файлу."""
    if default is None:
        default = {}
    path = _ROOT / name
    try:
        if not path.exists():
            return default
        mtime = path.stat().st_mtime
        hit = _cache.get(name)
        if hit and hit[0] == mtime:
            return hit[1]
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _cache[name] = (mtime, data)
        return data
    except Exception as e:
        logger.warning("load_json %s failed: %s", name, e)
        return default


def invalidate(name: str | None = None) -> None:
    if name is None:
        _cache.clear()
    else:
        _cache.pop(name, None)
