"""Їжа, готелі, банкомати, розмовні фрази."""

from __future__ import annotations

import json
from pathlib import Path

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, URLInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from locales import get_text, get_all_texts, get_user_lang, localize_field
from services.stats import log_button
from services.geo import nearby

router = Router()
ROOT = Path(__file__).parent.parent


def _load(name: str) -> dict:
    from services.data_cache import load_json
    return load_json(name, {})


def _maps_link(lat, lon) -> str:
    return f"https://www.google.com/maps?q={lat},{lon}"


# ---------- FOOD ----------
FOOD_TEXTS = set(get_all_texts("food_btn")) | {"🍽️ Де поїсти", "🍽️ Food", "Де поїсти", "Food"}


@router.message(F.text.in_(FOOD_TEXTS))
async def food_section(message: Message):
    log_button(message.from_user.id, "food")
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    data = _load("food.json")
    builder = InlineKeyboardBuilder()
    for cat in data.get("categories", []):
        title = cat.get(lang) or cat.get("uk") or cat["id"]
        builder.button(text=title, callback_data=f"food_cat:{cat['id']}")
    builder.button(text=get_text(user_id, "all_places"), callback_data="food_cat:all")
    builder.adjust(1)
    await message.answer(get_text(user_id, "food_section"), reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("food_cat:"))
async def food_by_category(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    cat_id = callback.data.split(":")[1]
    data = _load("food.json")
    places = data.get("places", [])
    if cat_id != "all":
        places = [p for p in places if p.get("category") == cat_id]
    # limit list size for telegram
    places = places[:40]
    if not places:
        await callback.answer(get_text(user_id, "no_food_nearby"), show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for p in places:
        builder.button(text=localize_field(p.get("name"), lang, "—")[:60], callback_data=f"food:{p['id']}")
    builder.button(text=get_text(user_id, "back"), callback_data="food_menu_back")
    builder.adjust(1)
    await callback.message.edit_text(get_text(user_id, "food_section"), reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "food_menu_back")
async def food_menu_back(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    data = _load("food.json")
    builder = InlineKeyboardBuilder()
    for cat in data.get("categories", []):
        title = cat.get(lang) or cat.get("uk") or cat["id"]
        builder.button(text=title, callback_data=f"food_cat:{cat['id']}")
    builder.button(text=get_text(user_id, "all_places"), callback_data="food_cat:all")
    builder.adjust(1)
    await callback.message.edit_text(get_text(user_id, "food_section"), reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("food:"))
async def food_detail(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    pid = int(callback.data.split(":")[1])
    place = next((p for p in _load("food.json").get("places", []) if p["id"] == pid), None)
    if not place:
        await callback.answer("—", show_alert=True)
        return
    name = localize_field(place.get("name"), lang)
    desc = localize_field(place.get("description"), lang)
    text = f"<b>{name}</b>\n\n{desc}\n\n"
    if place.get("lat") and place.get("lon"):
        text += f"📍 <a href='{_maps_link(place['lat'], place['lon'])}'>Google Maps</a>\n"
        # nearby ATMs
        atms = _load("atms.json").get("atms", [])
        near = nearby(atms, place["lat"], place["lon"], limit=5, max_m=2000)
        if near:
            text += "\n💳 <b>" + get_text(user_id, "nearby_atms") + ":</b>\n"
            for a, dist in near:
                an = localize_field(a.get("name"), lang)
                text += f"• {an} — {int(dist)} м\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="extra_back")]
    ])
    photo = place.get("photo") or ""
    try:
        if photo.startswith("http"):
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=URLInputFile(photo),
                caption=text,
                reply_markup=kb,
            )
        else:
            await callback.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    except Exception:
        await callback.message.answer(text, reply_markup=kb, disable_web_page_preview=True)
    await callback.answer()


# ---------- HOTELS ----------
HOTEL_TEXTS = set(get_all_texts("hotels_btn")) | {"🏨 Готелі", "🏨 Hotels", "Готелі", "Hotels"}


@router.message(F.text.in_(HOTEL_TEXTS))
async def hotels_section(message: Message):
    log_button(message.from_user.id, "hotels")
    user_id = message.from_user.id
    builder = InlineKeyboardBuilder()
    for stars in range(1, 6):
        builder.button(text=f"{'⭐' * stars} ({stars})", callback_data=f"hotel_star:{stars}")
    builder.button(text=get_text(user_id, "all_hotels"), callback_data="hotel_star:0")
    builder.adjust(1)
    await message.answer(get_text(user_id, "choose_hotel_stars"), reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("hotel_star:"))
async def hotels_by_star(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    stars = int(callback.data.split(":")[1])
    places = _load("hotels.json").get("places", [])
    if stars > 0:
        places = [p for p in places if int(p.get("stars") or 0) == stars]
    if not places:
        await callback.answer(get_text(user_id, "no_hotels_nearby"), show_alert=True)
        return
    builder = InlineKeyboardBuilder()
    for p in places[:40]:
        st = "⭐" * int(p.get("stars") or 0)
        title = localize_field(p.get("name"), lang, "—")
        builder.button(text=f"{st} {title}", callback_data=f"hotel:{p['id']}")
    builder.button(text=get_text(user_id, "back"), callback_data="hotels_menu_back")
    builder.adjust(1)
    await callback.message.edit_text(get_text(user_id, "hotels_section"), reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "hotels_menu_back")
async def hotels_menu_back(callback: CallbackQuery):
    user_id = callback.from_user.id
    builder = InlineKeyboardBuilder()
    for stars in range(1, 6):
        builder.button(text=f"{'⭐' * stars} ({stars})", callback_data=f"hotel_star:{stars}")
    builder.button(text=get_text(user_id, "all_hotels"), callback_data="hotel_star:0")
    builder.adjust(1)
    await callback.message.edit_text(get_text(user_id, "choose_hotel_stars"), reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("hotel:"))
async def hotel_detail(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    pid = int(callback.data.split(":")[1])
    place = next((p for p in _load("hotels.json").get("places", []) if p["id"] == pid), None)
    if not place:
        await callback.answer("—", show_alert=True)
        return
    name = localize_field(place.get("name"), lang)
    desc = localize_field(place.get("description"), lang)
    stars = place.get("stars") or 0
    text = f"<b>{name}</b> {'⭐' * stars}\n\n{desc}\n\n"
    if place.get("lat") and place.get("lon"):
        text += f"📍 <a href='{_maps_link(place['lat'], place['lon'])}'>Google Maps</a>\n"
        atms = _load("atms.json").get("atms", [])
        near = nearby(atms, place["lat"], place["lon"], limit=3, max_m=1000)
        if near:
            text += "\n💳 <b>" + get_text(user_id, "nearby_atms") + ":</b>\n"
            for a, dist in near:
                text += f"• {localize_field(a.get('name'), lang)} — {int(dist)} м\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="extra_back")]
    ])
    photo = place.get("photo") or ""
    try:
        if photo.startswith("http"):
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=URLInputFile(photo),
                caption=text,
                reply_markup=kb,
            )
        else:
            await callback.message.edit_text(text, reply_markup=kb, disable_web_page_preview=True)
    except Exception:
        await callback.message.answer(text, reply_markup=kb, disable_web_page_preview=True)
    await callback.answer()


# ---------- ATMs list ----------
ATM_TEXTS = set(get_all_texts("atms_btn")) | {"💳 Банкомати", "💳 ATMs", "Банкомати", "ATMs"}


@router.message(F.text.in_(ATM_TEXTS))
async def atms_section(message: Message):
    log_button(message.from_user.id, "atms")
    user_id = message.from_user.id
    await message.answer(get_text(user_id, "atms_hint"))


# ---------- PHRASES ----------
PHRASE_TEXTS = set(get_all_texts("phrases_btn")) | {
    "💬 Фрази", "💬 Phrases", "Фрази", "Phrases", "Розмовник",
}


@router.message(F.text.in_(PHRASE_TEXTS))
async def phrases_section(message: Message):
    log_button(message.from_user.id, "phrases")
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    data = _load("phrases.json")
    builder = InlineKeyboardBuilder()
    for cat in data.get("categories", []):
        title = cat.get(lang) or cat.get("uk") or cat["id"]
        builder.button(text=title, callback_data=f"phrase_cat:{cat['id']}")
    builder.adjust(1)
    await message.answer(get_text(user_id, "phrases_section"), reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("phrase_cat:"))
async def phrase_category(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    cat_id = callback.data.split(":")[1]
    data = _load("phrases.json")
    items = [p for p in data.get("phrases", []) if p.get("category") == cat_id]
    if not items:
        await callback.answer("—", show_alert=True)
        return
    lines = []
    for p in items:
        uk = p.get("uk", "")
        en = p.get("en", "")
        note = localize_field(p.get("note"), lang, "")
        if lang == "en":
            lines.append(f"<b>{en}</b>\n{uk}" + (f"\n<i>{note}</i>" if note else ""))
        else:
            lines.append(f"<b>{uk}</b>\n{en}" + (f"\n<i>{note}</i>" if note else ""))
    text = "\n\n".join(lines)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(user_id, "back"), callback_data="phrases_back")]
    ])
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "phrases_back")
async def phrases_back(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    data = _load("phrases.json")
    builder = InlineKeyboardBuilder()
    for cat in data.get("categories", []):
        title = cat.get(lang) or cat.get("uk") or cat["id"]
        builder.button(text=title, callback_data=f"phrase_cat:{cat['id']}")
    builder.adjust(1)
    await callback.message.edit_text(
        get_text(user_id, "phrases_section"),
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "extra_back")
async def extra_back(callback: CallbackQuery):
    from keyboards.menus import main_menu
    user_id = callback.from_user.id
    await callback.message.edit_text(get_text(user_id, "main_menu"))
    await callback.message.answer(get_text(user_id, "main_menu"), reply_markup=main_menu(user_id))
    await callback.answer()


# ---------- UPDATES / CHANGELOG ----------
UPDATES_TEXTS = set(get_all_texts("updates_btn")) | {
    "📰 Оновлення", "📰 Updates", "Оновлення", "Updates",
}


@router.message(F.text.in_(UPDATES_TEXTS))
async def updates_section(message: Message):
    log_button(message.from_user.id, "updates")
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    data = _load("changelog.json")
    updates = data.get("updates", [])
    if not updates:
        await message.answer(get_text(user_id, "updates_empty"))
        return

    lines = [get_text(user_id, "updates_title")]
    for u in updates:
        date = u.get("date", "")
        ver = u.get("version", "")
        items = u.get(lang) or u.get("uk") or []
        header = f"\n📅 <b>{date}</b> · v{ver}"
        body = "\n".join(f"• {item}" for item in items)
        lines.append(f"{header}\n{body}")

    text = "\n".join(lines)
    # Telegram message limit safety
    if len(text) > 4000:
        text = text[:3900] + "\n\n…"
    await message.answer(text)
