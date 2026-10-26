"""Гео-утиліти: відстань і пошук найближчих об'єктів."""

from __future__ import annotations

import math
from typing import Iterable


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def nearby(
    items: Iterable[dict],
    lat: float,
    lon: float,
    limit: int = 5,
    max_m: float = 1500,
) -> list[tuple[dict, float]]:
    """Повертає [(item, distance_m), ...] відсортовано за відстанню."""
    result: list[tuple[dict, float]] = []
    for it in items:
        ilat, ilon = it.get("lat"), it.get("lon")
        if ilat is None or ilon is None:
            continue
        try:
            d = haversine_m(lat, lon, float(ilat), float(ilon))
        except (TypeError, ValueError):
            continue
        if d <= max_m:
            result.append((it, d))
    result.sort(key=lambda x: x[1])
    return result[:limit]
