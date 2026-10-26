from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from locales import get_text, LANG_LABELS, SUPPORTED_LANGS
from config import CONTACT_URL


def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=get_text(user_id, "metro"))],
        [KeyboardButton(text=get_text(user_id, "places"))],
        [
            KeyboardButton(text=get_text(user_id, "food_btn")),
            KeyboardButton(text=get_text(user_id, "hotels_btn")),
        ],
        [
            KeyboardButton(text=get_text(user_id, "phrases_btn")),
            KeyboardButton(text=get_text(user_id, "atms_btn")),
        ],
        [KeyboardButton(text=get_text(user_id, "updates_btn")),
            KeyboardButton(text=get_text(user_id, "game_btn"))],
        [
            KeyboardButton(text=get_text(user_id, "alerts_btn")),
            KeyboardButton(text=get_text(user_id, "language_btn")),
        ],
        [
            KeyboardButton(text=get_text(user_id, "contacts_btn")),
            KeyboardButton(text=get_text(user_id, "help_btn")),
        ],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def places_menu(user_id: int) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text=get_text(user_id, "all_places"))],
        [KeyboardButton(text=get_text(user_id, "by_category"))],
        [KeyboardButton(text=get_text(user_id, "back"))],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def language_menu() -> InlineKeyboardMarkup:
    """Кнопки мов будуються з SUPPORTED_LANGS + LANG_LABELS — легко додати нову мову."""
    rows = []
    for code in SUPPORTED_LANGS:
        label = LANG_LABELS.get(code, code)
        rows.append([InlineKeyboardButton(text=label, callback_data=f"lang:{code}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def main_inline_menu(user_id: int) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=get_text(user_id, "metro"), callback_data="menu:metro")],
        [InlineKeyboardButton(text=get_text(user_id, "places"), callback_data="menu:places")],
        [
            InlineKeyboardButton(text=get_text(user_id, "food_btn"), callback_data="menu:food"),
            InlineKeyboardButton(text=get_text(user_id, "hotels_btn"), callback_data="menu:hotels"),
        ],
        [
            InlineKeyboardButton(text=get_text(user_id, "phrases_btn"), callback_data="menu:phrases"),
            InlineKeyboardButton(text=get_text(user_id, "updates_btn"), callback_data="menu:updates"),
        ],
        [InlineKeyboardButton(text=get_text(user_id, "alerts_btn"), callback_data="menu:alerts")],
        [InlineKeyboardButton(text=get_text(user_id, "game_btn"), callback_data="menu:game")],
        [InlineKeyboardButton(text=get_text(user_id, "contacts_btn"), callback_data="menu:contacts")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def contacts_keyboard(user_id: int) -> InlineKeyboardMarkup:
    rows = []
    if CONTACT_URL:
        rows.append([
            InlineKeyboardButton(
                text=get_text(user_id, "contacts_open"),
                url=CONTACT_URL,
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else InlineKeyboardMarkup(inline_keyboard=[])


def alerts_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=get_text(user_id, "alerts_on_btn"),
                callback_data="alert:on",
            ),
            InlineKeyboardButton(
                text=get_text(user_id, "alerts_off_btn"),
                callback_data="alert:off",
            ),
        ],
        [
            InlineKeyboardButton(
                text=get_text(user_id, "alerts_check_btn"),
                callback_data="alert:check",
            ),
        ],
    ])
