"""
Три рівні тривоги — суцільні кольорові картки (швидко, з кешем).

  green  — у Харківській області тривоги немає (і ніде / або є деінде — жовтий)
  yellow — у Харкові тихо, але в інших областях є тривога
  red    — тривога в Харківській області

Як працює: Pillow малює PNG у RAM (~5–15 KB), результат кешується.
"""

from __future__ import annotations

import io
import logging
from functools import lru_cache

logger = logging.getLogger("bot.alert_map")

# RGB fills
COLORS = {
    "green":  ((34, 139, 70),  (20, 90, 45),  (236, 255, 240)),
    "yellow": ((200, 160, 20), (140, 110, 10), (40, 30, 0)),
    "red":    ((180, 40, 40),  (110, 20, 20),  (255, 235, 235)),
}


@lru_cache(maxsize=16)
def _solid_card(level: str, title: str, subtitle: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    fill, border, text_c = COLORS.get(level, COLORS["green"])
    W, H = 720, 400
    img = Image.new("RGB", (W, H), fill)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W - 1, H - 1], outline=border, width=8)

    try:
        font_lg = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36
        )
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22
        )
    except Exception:
        font_lg = font = ImageFont.load_default()

    # center text
    draw.text((W // 2, H // 2 - 30), title, fill=text_c, font=font_lg, anchor="mm")
    draw.text((W // 2, H // 2 + 30), subtitle, fill=text_c, font=font, anchor="mm")

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def build_level_card(level: str, lang: str = "uk") -> bytes | None:
    """level: green | yellow | red"""
    try:
        if lang == "en":
            titles = {
                "green": "ALL CLEAR",
                "yellow": "ALERT ELSEWHERE",
                "red": "AIR RAID ALERT",
            }
            subs = {
                "green": "Kharkiv oblast — no alert",
                "yellow": "Kharkiv oblast is safe · other regions under alert",
                "red": "Kharkiv oblast — take shelter!",
            }
        else:
            titles = {
                "green": "БЕЗ ТРИВОГИ",
                "yellow": "ТРИВОГА В ІНШИХ РЕГІОНАХ",
                "red": "ПОВІТРЯНА ТРИВОГА",
            }
            subs = {
                "green": "Харківська область — спокійно",
                "yellow": "Харків у безпеці · тривога в інших областях",
                "red": "Харківська область — пройдіть в укриття!",
            }
        return _solid_card(level, titles.get(level, level), subs.get(level, ""))
    except Exception as e:
        logger.warning("level card failed: %s", e)
        return None


def build_kharkiv_clear_card(lang: str = "uk", other_count: int = 0) -> bytes | None:
    level = "yellow" if other_count > 0 else "green"
    return build_level_card(level, lang)


def build_alert_scheme_png(active_ids: list[int], **kwargs) -> bytes | None:
    others = [i for i in active_ids if i != 19]
    return build_kharkiv_clear_card(kwargs.get("lang", "uk"), len(others))
