"""Гра: вгадай станцію метро за фото."""

from __future__ import annotations

import random
from pathlib import Path

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, FSInputFile,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from locales import get_text, get_all_texts, get_user_lang, localize_field
from services.stats import log_button
from services.data_cache import load_json

router = Router()
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# user_id -> consecutive correct answers
_scores: dict[int, int] = {}


def _resolve_station_photo(photo_file: str) -> Path | None:
    if not photo_file:
        return None
    name = Path(photo_file).name
    for p in (
        PROJECT_ROOT / "data" / "maps" / name,
        PROJECT_ROOT / "data" / "stations" / name,
        PROJECT_ROOT / photo_file,
        PROJECT_ROOT / "data" / photo_file,
    ):
        if p.exists():
            return p
    return None


def _stations_with_photos() -> list[dict]:
    data = load_json("metro.json", {"stations": []})
    out = []
    for s in data.get("stations", []):
        path = _resolve_station_photo(s.get("photo") or "")
        if path:
            out.append({**s, "_photo_path": str(path)})
    return out


def _round_keyboard(correct_id: int, options: list[dict], lang: str) -> InlineKeyboardMarkup:
    rows = []
    for s in options:
        name = localize_field(s.get("name"), lang, "?")
        rows.append([
            InlineKeyboardButton(
                text=name,
                callback_data=f"game_ans:{correct_id}:{s['id']}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def start_round(target, user_id: int) -> None:
    """Надіслати нове питання (фото + варіанти)."""
    lang = get_user_lang(user_id)
    pool = _stations_with_photos()
    if len(pool) < 4:
        await target.answer(get_text(user_id, "game_no_photos"))
        return

    correct = random.choice(pool)
    others = [s for s in pool if s["id"] != correct["id"]]
    wrong = random.sample(others, k=min(3, len(others)))
    options = wrong + [correct]
    random.shuffle(options)

    score = _scores.get(user_id, 0)
    caption = get_text(user_id, "game_section")
    if score:
        caption += "\n" + get_text(user_id, "game_score", score=score)

    kb = _round_keyboard(correct["id"], options, lang)
    await target.answer_photo(
        photo=FSInputFile(correct["_photo_path"]),
        caption=caption,
        reply_markup=kb,
    )


@router.message(F.text.in_(get_all_texts("game_btn")))
async def game_entry(message: Message):
    user_id = message.from_user.id
    log_button(user_id, "game")
    await start_round(message, user_id)


@router.callback_query(F.data == "game:again")
async def game_again(callback: CallbackQuery):
    await callback.answer()
    await start_round(callback.message, callback.from_user.id)


@router.callback_query(F.data.startswith("game_ans:"))
async def game_answer(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    parts = callback.data.split(":")
    try:
        correct_id = int(parts[1])
        chosen_id = int(parts[2])
    except (IndexError, ValueError):
        await callback.answer("—", show_alert=True)
        return

    data = load_json("metro.json", {"stations": []})
    station = next((s for s in data.get("stations", []) if s["id"] == correct_id), None)
    name = localize_field(station.get("name"), lang, "?") if station else "?"

    if chosen_id == correct_id:
        _scores[user_id] = _scores.get(user_id, 0) + 1
        log_button(user_id, "game:correct")
        result = get_text(user_id, "game_correct", name=name)
        result += "\n" + get_text(user_id, "game_score", score=_scores[user_id])
    else:
        _scores[user_id] = 0
        log_button(user_id, "game:wrong")
        result = get_text(user_id, "game_wrong", name=name)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=get_text(user_id, "game_again"),
            callback_data="game:again",
        )]
    ])
    try:
        if callback.message.photo:
            await callback.message.edit_caption(caption=result, reply_markup=kb)
        else:
            await callback.message.edit_text(result, reply_markup=kb)
    except Exception:
        await callback.message.answer(result, reply_markup=kb)
    await callback.answer()
