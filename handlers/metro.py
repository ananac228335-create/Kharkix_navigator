from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile, InputMediaPhoto
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pathlib import Path
import logging

from locales import get_text, get_all_texts, get_user_lang, localize_field
from services.stats import log_button
from services.schedule import format_schedule
from services.geo import nearby
from services.data_cache import load_json

logger = logging.getLogger("bot.metro")
router = Router()

PROJECT_ROOT = Path(__file__).parent.parent
MAPS_DIR = PROJECT_ROOT / "data" / "maps"

# Кандидати на схему метро (файл може мати різну назву)
_MAP_CANDIDATES = [
    "karta-metro-kharkiv.png",
    "karta-metro-hakkov.png",
    "karta-metro.png",
    "metro-map.png",
    "metro.png",
    "map.png",
]


def resolve_map_path() -> Path | None:
    for name in _MAP_CANDIDATES:
        p = MAPS_DIR / name
        if p.exists():
            return p
    # будь-який png/jpg з "metro" або "karta" у назві
    if MAPS_DIR.exists():
        for p in sorted(MAPS_DIR.iterdir()):
            low = p.name.lower()
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and (
                "metro" in low or "karta" in low or "map" in low
            ):
                return p
    return None


def load_metro_data():
    return load_json("metro.json", {"lines": [], "stations": []})


def load_places_data():
    return load_json("places.json", {"places": []})


def _localized(value, lang: str, default: str = ""):
    return localize_field(value, lang, default)


def get_lines_keyboard() -> InlineKeyboardMarkup:
    data = load_metro_data()
    builder = InlineKeyboardBuilder()
    for line in data.get("lines", []):
        builder.button(text=line["name"], callback_data=f"line:{line['id']}")
    # bilingual label for mixed audience
    builder.button(text="🕐 Schedule / Розклад", callback_data="metro_schedule")
    builder.adjust(1)
    return builder.as_markup()


def get_stations_keyboard(line_id: int, user_id: int) -> InlineKeyboardMarkup:
    data = load_metro_data()
    builder = InlineKeyboardBuilder()
    lang = get_user_lang(user_id)

    stations = [s for s in data.get("stations", []) if s["line_id"] == line_id]
    for station in stations:
        name = _localized(station.get("name"), lang, "Station")
        builder.button(text=name, callback_data=f"station:{station['id']}")

    builder.button(text=get_text(user_id, "back"), callback_data="back_to_lines")
    builder.adjust(1)
    return builder.as_markup()


def resolve_photo(photo_file: str) -> Path | None:
    if not photo_file:
        return None
    candidates = [
        PROJECT_ROOT / photo_file,
        PROJECT_ROOT / "data" / "stations" / Path(photo_file).name,
        PROJECT_ROOT / "data" / "maps" / Path(photo_file).name,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def station_detail_keyboard(station: dict, user_id: int) -> InlineKeyboardMarkup:
    places = load_places_data().get("places", [])
    sid = station["id"]
    has_nearby = any(sid in (p.get("station_ids") or []) for p in places)

    rows = []
    if has_nearby:
        rows.append([InlineKeyboardButton(
            text=get_text(user_id, "nearby_places"),
            callback_data=f"nearby:{sid}"
        )])
    rows.append([InlineKeyboardButton(
        text=get_text(user_id, "station_services"),
        callback_data=f"st_services:{sid}"
    )])
    rows.append([
        InlineKeyboardButton(text=get_text(user_id, "nearby_food"), callback_data=f"st_food:{sid}"),
        InlineKeyboardButton(text=get_text(user_id, "nearby_hotels"), callback_data=f"st_hotels:{sid}"),
    ])
    rows.append([InlineKeyboardButton(
        text=get_text(user_id, "schedule_btn"),
        callback_data="metro_schedule"
    )])
    rows.append([InlineKeyboardButton(
        text=get_text(user_id, "back"),
        callback_data=f"line:{station['line_id']}"
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _safe_edit(callback: CallbackQuery, text: str, reply_markup=None):
    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, reply_markup=reply_markup)
        else:
            await callback.message.edit_text(text=text, reply_markup=reply_markup)
    except Exception as e:
        logger.debug("edit failed, fallback answer: %s", e)
        await callback.message.answer(text, reply_markup=reply_markup)


@router.message(F.text.in_(get_all_texts("metro")))
async def metro_section(message: Message):
    log_button(message.from_user.id, "🚇 Метро")
    user_id = message.from_user.id
    map_path = resolve_map_path()

    if map_path:
        await message.answer_photo(
            photo=FSInputFile(map_path),
            caption=get_text(user_id, "choose_line"),
            reply_markup=get_lines_keyboard()
        )
    else:
        await message.answer(
            get_text(user_id, "choose_line"),
            reply_markup=get_lines_keyboard()
        )


@router.callback_query(F.data == "metro_schedule")
async def show_schedule(callback: CallbackQuery):
    log_button(callback.from_user.id, "расписание")
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    text = format_schedule(lang)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="back_to_lines")]
    ])
    await _safe_edit(callback, text, kb)
    await callback.answer()


@router.callback_query(F.data.startswith("line:"))
async def show_stations(callback: CallbackQuery):
    log_button(callback.from_user.id, f"линия:{callback.data}")
    user_id = callback.from_user.id
    try:
        line_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("—", show_alert=True)
        return
    data = load_metro_data()
    line = next((l for l in data.get("lines", []) if l["id"] == line_id), None)
    line_name = line["name"] if line else "—"
    text = f"<b>{line_name}</b>\n\n{get_text(user_id, 'choose_station')}"
    kb = get_stations_keyboard(line_id, user_id)
    await _safe_edit(callback, text, kb)
    await callback.answer()


@router.callback_query(F.data.startswith("station:"))
async def show_station_info(callback: CallbackQuery):
    log_button(callback.from_user.id, f"станция:{callback.data}")
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    try:
        station_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer(get_text(user_id, "station_not_found"), show_alert=True)
        return
    data = load_metro_data()
    station = next((s for s in data.get("stations", []) if s["id"] == station_id), None)
    if not station:
        await callback.answer(get_text(user_id, "station_not_found"), show_alert=True)
        return

    station_name = _localized(station.get("name"), lang, "—")
    description = _localized(station.get("description"), lang, "—")
    text = f"<b>{station_name}</b>\n\n{description}\n\n"

    lat, lon = station.get("lat"), station.get("lon")
    if lat and lon:
        text += f"📍 <a href='https://www.google.com/maps?q={lat},{lon}'>Google Maps</a>\n"
        try:
            atms = load_json("atms.json", {}).get("atms", [])
            near = nearby(atms, float(lat), float(lon), limit=5, max_m=2000)
            if near:
                text += "\n💳 <b>" + get_text(user_id, "nearby_atms") + ":</b>\n"
                for a, dist in near:
                    an = _localized(a.get("name"), lang)
                    a_lat = a.get("lat")
                    a_lon = a.get("lon")
                    text += f"• {an} — {int(dist)} м\n"
                    if a_lat and a_lon:
                        text += f"  <a href='https://www.google.com/maps?q={a_lat},{a_lon}'>карта</a>\n"
        except Exception as e:
            logger.warning("atms near station: %s", e)
        try:
            svc = load_json("station_services.json", {})
            items = svc.get("by_station", {}).get(str(station_id), [])[:2]
            if items:
                text += "\n🏪 "
                text += "; ".join((it.get(lang) or it.get("uk") or "") for it in items)
                text += "\n"
        except Exception as e:
            logger.warning("station services: %s", e)

    keyboard = station_detail_keyboard(station, user_id)
    photo_path = resolve_photo(station.get("photo", ""))

    if photo_path:
        media = InputMediaPhoto(media=FSInputFile(photo_path), caption=text)
        try:
            await callback.message.edit_media(media=media, reply_markup=keyboard)
        except Exception as e:
            logger.debug("edit_media failed: %s", e)
            await _safe_edit(callback, text, keyboard)
    else:
        await _safe_edit(callback, text, keyboard)

    await callback.answer()


@router.callback_query(F.data.startswith("nearby:"))
async def show_nearby_places(callback: CallbackQuery):
    log_button(callback.from_user.id, f"рядом:{callback.data}")
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    try:
        station_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("—", show_alert=True)
        return

    places = [
        p for p in load_places_data().get("places", [])
        if station_id in (p.get("station_ids") or [])
    ]

    if not places:
        await callback.answer(get_text(user_id, "no_nearby"), show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for p in places:
        name = _localized(p.get("name"), lang, "Place")
        builder.button(text=name, callback_data=f"place:{p['id']}")
    builder.button(text=get_text(user_id, "back"), callback_data=f"station:{station_id}")
    builder.adjust(1)

    text = get_text(user_id, "nearby_places") + ":"
    await _safe_edit(callback, text, builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "back_to_lines")
async def back_to_lines(callback: CallbackQuery):
    log_button(callback.from_user.id, "назад_к_линиям")
    user_id = callback.from_user.id
    map_path = resolve_map_path()
    caption = get_text(user_id, "choose_line")
    kb = get_lines_keyboard()

    if map_path and callback.message.photo:
        media = InputMediaPhoto(media=FSInputFile(map_path), caption=caption)
        try:
            await callback.message.edit_media(media=media, reply_markup=kb)
        except Exception as e:
            logger.debug("back_to_lines media: %s", e)
            await _safe_edit(callback, caption, kb)
    else:
        await _safe_edit(callback, caption, kb)
    await callback.answer()


@router.callback_query(F.data.startswith("st_food:"))
async def station_food(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    try:
        sid = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("—", show_alert=True)
        return
    log_button(user_id, f"st_food:{sid}")
    data = load_metro_data()
    station = next((s for s in data.get("stations", []) if s["id"] == sid), None)
    if not station or not station.get("lat") or not station.get("lon"):
        await callback.answer(get_text(user_id, "no_food_nearby"), show_alert=True)
        return
    food = load_json("food.json", {}).get("places", [])
    near = nearby(food, float(station["lat"]), float(station["lon"]), limit=12, max_m=4000)
    if not near:
        await callback.answer(get_text(user_id, "no_food_nearby"), show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for item, dist in near:
        title = _localized(item.get("name"), lang, "—")
        builder.button(text=f"{title} ({int(dist)} м)", callback_data=f"food:{item['id']}")
    builder.button(text=get_text(user_id, "back"), callback_data=f"station:{sid}")
    builder.adjust(1)
    text = get_text(user_id, "nearby_food") + ":"
    await _safe_edit(callback, text, builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("st_hotels:"))
async def station_hotels_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        sid = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("—", show_alert=True)
        return
    log_button(user_id, f"st_hotels:{sid}")
    builder = InlineKeyboardBuilder()
    for stars in range(1, 6):
        builder.button(text="⭐" * stars, callback_data=f"st_hotel_star:{sid}:{stars}")
    builder.button(text=get_text(user_id, "all_hotels"), callback_data=f"st_hotel_star:{sid}:0")
    builder.button(text=get_text(user_id, "back"), callback_data=f"station:{sid}")
    builder.adjust(1)
    await _safe_edit(callback, get_text(user_id, "choose_hotel_stars"), builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("st_hotel_star:"))
async def station_hotels_list(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    parts = callback.data.split(":")
    try:
        sid = int(parts[1])
        stars = int(parts[2])
    except (ValueError, IndexError):
        await callback.answer("—", show_alert=True)
        return
    data = load_metro_data()
    station = next((s for s in data.get("stations", []) if s["id"] == sid), None)
    if not station or not station.get("lat") or not station.get("lon"):
        await callback.answer(get_text(user_id, "no_hotels_nearby"), show_alert=True)
        return
    hotels = load_json("hotels.json", {}).get("places", [])
    near = nearby(hotels, float(station["lat"]), float(station["lon"]), limit=12, max_m=4000)
    if stars > 0:
        near = [(h, d) for h, d in near if int(h.get("stars") or 0) == stars]
    if not near:
        await callback.answer(get_text(user_id, "no_hotels_nearby"), show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for item, dist in near:
        title = _localized(item.get("name"), lang, "—")
        st = "⭐" * int(item.get("stars") or 0)
        builder.button(text=f"{st} {title} ({int(dist)} м)", callback_data=f"hotel:{item['id']}")
    builder.button(text=get_text(user_id, "back"), callback_data=f"st_hotels:{sid}")
    builder.adjust(1)
    text = get_text(user_id, "nearby_hotels") + ":"
    await _safe_edit(callback, text, builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("st_services:"))
async def station_services(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    try:
        sid = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("—", show_alert=True)
        return
    log_button(user_id, f"st_services:{sid}")
    data = load_json("station_services.json", {})
    items = data.get("by_station", {}).get(str(sid), [])
    if not items:
        await callback.answer(get_text(user_id, "no_nearby"), show_alert=True)
        return
    lines = []
    for it in items:
        lines.append("• " + (it.get(lang) or it.get("uk") or "—"))
    text = get_text(user_id, "station_services") + "\n\n" + "\n".join(lines)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data=f"station:{sid}")]
    ])
    await _safe_edit(callback, text, kb)
    await callback.answer()
