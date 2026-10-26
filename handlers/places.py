from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile, InputMediaPhoto
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
from pathlib import Path

from keyboards.menus import places_menu
from locales import get_text, get_all_texts, get_user_lang, localize_field
from services.stats import log_button
from services.geo import nearby

router = Router()
DATA_PATH = Path(__file__).parent.parent / "data" / "places.json"
PROJECT_ROOT = Path(__file__).parent.parent


def load_places_data():
    from services.data_cache import load_json
    return load_json("places.json", {"categories": [], "places": []})


def _localized(value, lang: str, default: str = ""):
    return localize_field(value, lang, default)


def get_categories_keyboard(user_id: int) -> InlineKeyboardMarkup:
    data = load_places_data()
    lang = get_user_lang(user_id)
    builder = InlineKeyboardBuilder()
    for cat in data.get("categories", []):
        title = cat.get(lang) or cat.get("uk") or cat.get("ru") or cat.get("id")
        builder.button(text=title, callback_data=f"place_cat:{cat['id']}")
    builder.button(text=get_text(user_id, "all_places"), callback_data="place_cat:all")
    builder.button(text=get_text(user_id, "back"), callback_data="places_back_menu")
    builder.adjust(1)
    return builder.as_markup()


def get_places_list_keyboard(places: list, user_id: int, back_data: str = "places_categories") -> InlineKeyboardMarkup:
    lang = get_user_lang(user_id)
    builder = InlineKeyboardBuilder()
    for place in places:
        name = _localized(place.get("name"), lang, "Place")
        builder.button(text=name, callback_data=f"place:{place['id']}")
    builder.button(text=get_text(user_id, "back"), callback_data=back_data)
    builder.adjust(1)
    return builder.as_markup()


def resolve_photo(photo_file: str) -> Path | None:
    if not photo_file:
        return None
    name = Path(photo_file).name
    candidates = [
        PROJECT_ROOT / photo_file,
        PROJECT_ROOT / "data" / photo_file,  # data/places_photos/1.jpg
        PROJECT_ROOT / "data" / "places_photos" / name,
        PROJECT_ROOT / "data" / "places_photos" / "places_photos" / name,  # nested
        PROJECT_ROOT / "data" / "places" / name,
        PROJECT_ROOT / "data" / "maps" / name,
        PROJECT_ROOT / "data" / "stations" / name,
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


# Тексти кнопок (усі мови + старі варіанти, щоб не було "not handled")
PLACES_TEXTS = set(get_all_texts("places")) | {
    "📍 Цікаві місця", "📍 Places", "📍 Интересные места",
    "Цікаві місця", "Places", "Интересные места",
}
ALL_PLACES_TEXTS = set(get_all_texts("all_places")) | {
    "Усі місця", "All places", "Все места",
}
BY_CATEGORY_TEXTS = set(get_all_texts("by_category")) | {
    "За категоріями", "By category", "По категориям",
}


@router.message(F.text.in_(PLACES_TEXTS))
async def places_section(message: Message):
    log_button(message.from_user.id, "📍 places")
    user_id = message.from_user.id
    await message.answer(
        get_text(user_id, "places_section"),
        reply_markup=places_menu(user_id),
    )


@router.message(F.text.in_(ALL_PLACES_TEXTS))
async def all_places(message: Message):
    log_button(message.from_user.id, "all_places")
    user_id = message.from_user.id
    data = load_places_data()
    places = data.get("places", [])
    if not places:
        await message.answer(get_text(user_id, "no_places"))
        return
    await message.answer(
        get_text(user_id, "choose_place"),
        reply_markup=get_places_list_keyboard(places, user_id, back_data="places_categories"),
    )


@router.message(F.text.in_(BY_CATEGORY_TEXTS))
async def places_by_category(message: Message):
    log_button(message.from_user.id, "by_category")
    user_id = message.from_user.id
    await message.answer(
        get_text(user_id, "choose_category"),
        reply_markup=get_categories_keyboard(user_id),
    )


@router.callback_query(F.data == "places_categories")
async def cb_places_categories(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.edit_text(
        get_text(user_id, "choose_category"),
        reply_markup=get_categories_keyboard(user_id)
    )
    await callback.answer()


@router.callback_query(F.data == "places_back_menu")
async def cb_places_back_menu(callback: CallbackQuery):
    from keyboards.menus import main_menu
    user_id = callback.from_user.id
    await callback.message.edit_text(get_text(user_id, "main_menu"))
    await callback.message.answer(
        get_text(user_id, "main_menu"),
        reply_markup=main_menu(user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("place_cat:"))
async def cb_place_category(callback: CallbackQuery):
    user_id = callback.from_user.id
    cat_id = callback.data.split(":", 1)[1]
    data = load_places_data()
    places = data.get("places", [])
    if cat_id != "all":
        places = [p for p in places if p.get("category") == cat_id]

    if not places:
        await callback.answer(get_text(user_id, "no_places"), show_alert=True)
        return

    await callback.message.edit_text(
        get_text(user_id, "choose_place"),
        reply_markup=get_places_list_keyboard(places, user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("place:"))
async def cb_show_place(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    place_id = int(callback.data.split(":")[1])
    log_button(user_id, f"место:{place_id}")

    data = load_places_data()
    place = next((p for p in data.get("places", []) if p["id"] == place_id), None)
    if not place:
        await callback.answer(get_text(user_id, "place_not_found"), show_alert=True)
        return

    name = _localized(place.get("name"), lang, "—")
    desc = _localized(place.get("description"), lang, "")
    text = f"<b>{name}</b>\n\n{desc}\n\n"

    lat, lon = place.get("lat"), place.get("lon")
    if lat and lon:
        text += f"📍 <a href='https://www.google.com/maps?q={lat},{lon}'>Google Maps</a>\n"
        try:
            import json as _json
            _atms = _json.load(open(PROJECT_ROOT / 'data' / 'atms.json', encoding='utf-8')).get('atms', [])
            _near = nearby(_atms, float(lat), float(lon), limit=5, max_m=2000)
            if _near:
                text += '\n💳 <b>' + get_text(user_id, 'nearby_atms') + ':</b>\n'
                for _a, _d in _near:
                    text += f"• {_localized(_a.get('name'), lang)} — {int(_d)} м\n"
        except Exception:
            pass

    # Связанные станции
    station_ids = place.get("station_ids") or []
    buttons = []
    if station_ids:
        buttons.append([InlineKeyboardButton(
            text=get_text(user_id, "nearby_stations"),
            callback_data=f"place_stations:{place_id}"
        )])
    buttons.append([InlineKeyboardButton(
        text=get_text(user_id, "nearby_food"),
        callback_data=f"place_food:{place_id}"
    )])
    buttons.append([InlineKeyboardButton(
        text=get_text(user_id, "back"),
        callback_data="places_categories"
    )])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    photo_path = resolve_photo(place.get("photo", ""))
    if photo_path and callback.message.photo:
        media = InputMediaPhoto(media=FSInputFile(photo_path), caption=text)
        await callback.message.edit_media(media=media, reply_markup=keyboard)
    elif photo_path:
        # сообщение было текстовым — отправим новое с фото
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=FSInputFile(photo_path),
            caption=text,
            reply_markup=keyboard
        )
    else:
        if callback.message.photo:
            await callback.message.edit_caption(caption=text, reply_markup=keyboard)
        else:
            await callback.message.edit_text(text=text, reply_markup=keyboard)

    await callback.answer()


@router.callback_query(F.data.startswith("place_stations:"))
async def cb_place_stations(callback: CallbackQuery):
    """Станции рядом с местом."""
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    place_id = int(callback.data.split(":")[1])

    places_data = load_places_data()
    place = next((p for p in places_data.get("places", []) if p["id"] == place_id), None)
    if not place:
        await callback.answer(get_text(user_id, "place_not_found"), show_alert=True)
        return

    metro_path = PROJECT_ROOT / "data" / "metro.json"
    with open(metro_path, "r", encoding="utf-8") as f:
        metro = json.load(f)

    station_ids = set(place.get("station_ids") or [])
    stations = [s for s in metro.get("stations", []) if s["id"] in station_ids]

    builder = InlineKeyboardBuilder()
    for s in stations:
        sname = _localized(s.get("name"), lang, str(s["id"]))
        builder.button(text=f"🚇 {sname}", callback_data=f"station:{s['id']}")
    builder.button(text=get_text(user_id, "back"), callback_data=f"place:{place_id}")
    builder.adjust(1)

    text = get_text(user_id, "nearby_stations") + ":"
    kb = builder.as_markup()
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, reply_markup=kb)
    else:
        await callback.message.edit_text(text=text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("place_food:"))
async def place_nearby_food(callback: CallbackQuery):
    from services.geo import nearby
    import json as _json
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    place_id = int(callback.data.split(":")[1])
    data = load_places_data()
    place = next((p for p in data.get("places", []) if p["id"] == place_id), None)
    if not place or not place.get("lat"):
        await callback.answer(get_text(user_id, "no_food_nearby"), show_alert=True)
        return
    food = _json.load(open(PROJECT_ROOT / "data" / "food.json", encoding="utf-8")).get("places", [])
    near = nearby(food, float(place["lat"]), float(place["lon"]), limit=8, max_m=2500)
    if not near:
        await callback.answer(get_text(user_id, "no_food_nearby"), show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for item, dist in near:
        title = _localized(item.get("name"), lang, "—")
        builder.button(text=f"{title} ({int(dist)}м)", callback_data=f"food:{item['id']}")
    builder.button(text=get_text(user_id, "back"), callback_data=f"place:{place_id}")
    builder.adjust(1)
    text = get_text(user_id, "nearby_food") + ":"
    if callback.message.photo:
        await callback.message.edit_caption(caption=text, reply_markup=builder.as_markup())
    else:
        await callback.message.edit_text(text=text, reply_markup=builder.as_markup())
    await callback.answer()
