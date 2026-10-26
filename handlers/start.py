from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command

from keyboards.menus import (
    main_menu, language_menu, main_inline_menu,
    contacts_keyboard, alerts_keyboard,
)
from locales import get_text, set_language, user_languages, get_all_texts, get_user_lang
from services.stats import get_stats, log_button
from services.alerts import (
    subscribe, unsubscribe, is_subscribed, get_current_status_text,
    send_current_status_if_active,
)
from config import ADMIN_IDS, CONTACT_URL, CONTACT_USERNAME

router = Router()

async def _safe_edit_or_answer(callback, text: str, reply_markup=None):
    """edit_text fails on photo messages — fallback to caption or new message."""
    msg = callback.message
    try:
        if msg.photo:
            await msg.edit_caption(caption=text, reply_markup=reply_markup)
        else:
            await msg.edit_text(text, reply_markup=reply_markup)
    except Exception:
        await msg.answer(text, reply_markup=reply_markup)



async def _show_alerts_menu(message_or_cb, user_id: int, edit: bool = False):
    from services.alerts import get_status_payload
    from aiogram.types import BufferedInputFile
    from locales import t
    status_key = "alerts_status_on" if is_subscribed(user_id) else "alerts_status_off"
    status = get_text(user_id, status_key)
    lang = get_user_lang(user_id)
    payload = await get_status_payload(lang)
    live = payload["text"]
    png = payload.get("png")
    text = f"{live}\n\n" + get_text(user_id, "alerts_info", status=status)
    kb = alerts_keyboard(user_id)
    target = message_or_cb if isinstance(message_or_cb, Message) else message_or_cb.message
    if png:
        caption = text[:1024]
        await target.answer_photo(
            photo=BufferedInputFile(png, filename="alert_scheme.png"),
            caption=caption,
            reply_markup=kb,
        )
    elif edit and hasattr(message_or_cb, "message"):
        try:
            await message_or_cb.message.edit_text(text, reply_markup=kb)
        except Exception:
            await target.answer(text, reply_markup=kb)
    else:
        await target.answer(text, reply_markup=kb)


@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    log_button(user_id, "/start")

    if user_id not in user_languages:
        await message.answer(
            get_text(user_id, "choose_language"),
            reply_markup=language_menu(),
        )
    else:
        await message.answer(
            get_text(user_id, "start"),
            reply_markup=main_menu(user_id),
        )
        await message.answer(
            get_text(user_id, "main_menu"),
            reply_markup=main_inline_menu(user_id),
        )


@router.message(Command("help"))
@router.message(F.text.in_(get_all_texts("help_btn")))
async def cmd_help(message: Message):
    log_button(message.from_user.id, "help")
    await message.answer(get_text(message.from_user.id, "help"))


@router.message(F.text.in_(get_all_texts("language_btn")))
async def change_language(message: Message):
    log_button(message.from_user.id, "language")
    await message.answer(
        get_text(message.from_user.id, "choose_language"),
        reply_markup=language_menu(),
    )


@router.callback_query(F.data.startswith("lang:"))
async def process_language(callback: CallbackQuery):
    user_id = callback.from_user.id
    lang = callback.data.split(":")[1]
    set_language(user_id, lang)
    log_button(user_id, f"lang:{lang}")

    await callback.message.edit_text(get_text(user_id, "language_changed"))
    await callback.message.answer(
        get_text(user_id, "start"),
        reply_markup=main_menu(user_id),
    )
    await callback.message.answer(
        get_text(user_id, "main_menu"),
        reply_markup=main_inline_menu(user_id),
    )
    await callback.answer()


@router.message(F.text.in_(get_all_texts("back")))
async def back_to_main(message: Message):
    user_id = message.from_user.id
    log_button(user_id, "back")

    if user_id not in user_languages:
        await message.answer(
            get_text(user_id, "choose_language"),
            reply_markup=language_menu(),
        )
    else:
        await message.answer(
            get_text(user_id, "main_menu"),
            reply_markup=main_menu(user_id),
        )


# ===== Тривога =====
@router.message(Command("alerts"))
@router.message(F.text.in_(get_all_texts("alerts_btn")))
async def alerts_menu(message: Message):
    user_id = message.from_user.id
    log_button(user_id, "alerts")
    await _show_alerts_menu(message, user_id)


@router.message(Command("status"))
async def cmd_status(message: Message):
    """Перевірити, чи є тривога ЗАРАЗ (разовий запит до API)."""
    from services.alerts import get_status_payload
    from aiogram.types import BufferedInputFile
    from locales import t, get_user_lang
    user_id = message.from_user.id
    log_button(user_id, "/status")
    wait = await message.answer(get_text(user_id, "status_checking"))
    lang = get_user_lang(user_id)
    payload = await get_status_payload(lang)
    text = payload["text"]
    png = payload.get("png")
    try:
        await wait.delete()
    except Exception:
        pass
    if png:
        caption = text[:1024]
        await message.answer_photo(
            photo=BufferedInputFile(png, filename="alert_scheme.png"),
            caption=caption,
        )
    else:
        await message.answer(text)


@router.callback_query(F.data == "alert:on")
async def enable_alerts(callback: CallbackQuery):
    user_id = callback.from_user.id
    subscribe(user_id)
    log_button(user_id, "alert:on")
    await _safe_edit_or_answer(callback, get_text(user_id, "alerts_enabled"), alerts_keyboard(user_id))
    await callback.answer()
    await send_current_status_if_active(callback.bot, user_id)


@router.callback_query(F.data == "alert:off")
async def disable_alerts(callback: CallbackQuery):
    user_id = callback.from_user.id
    unsubscribe(user_id)
    log_button(user_id, "alert:off")
    await _safe_edit_or_answer(callback, get_text(user_id, "alerts_disabled"), alerts_keyboard(user_id))
    await callback.answer()


@router.callback_query(F.data == "alert:check")
async def check_alert_now(callback: CallbackQuery):
    """Кнопка «Перевірити зараз» — актуальний статус з API (+ схема якщо треба)."""
    from services.alerts import get_status_payload
    from aiogram.types import BufferedInputFile
    from locales import t
    user_id = callback.from_user.id
    log_button(user_id, "alert:check")
    await callback.answer(get_text(user_id, "status_checking"))
    lang = get_user_lang(user_id)
    payload = await get_status_payload(lang)
    live = payload["text"]
    png = payload.get("png")
    status_key = "alerts_status_on" if is_subscribed(user_id) else "alerts_status_off"
    status = get_text(user_id, status_key)
    text = f"{live}\n\n" + get_text(user_id, "alerts_info", status=status)
    if png:
        caption = text[:1024]
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            photo=BufferedInputFile(png, filename="alert_scheme.png"),
            caption=caption,
            reply_markup=alerts_keyboard(user_id),
        )
    else:
        try:
            await callback.message.edit_text(text, reply_markup=alerts_keyboard(user_id))
        except Exception:
            await callback.message.answer(text, reply_markup=alerts_keyboard(user_id))


# ===== Контакти =====
@router.message(F.text.in_(get_all_texts("contacts_btn")))
async def contacts_message(message: Message):
    user_id = message.from_user.id
    log_button(user_id, "contacts")
    link = CONTACT_URL or (f"@{CONTACT_USERNAME}" if CONTACT_USERNAME else "—")
    text = (
        get_text(user_id, "contacts_title")
        + "\n\n"
        + get_text(user_id, "contacts_body", extra=get_text(user_id, "contacts_extra"), link=link)
    )
    await message.answer(text, reply_markup=contacts_keyboard(user_id), disable_web_page_preview=True)


# ===== Статистика (лише для розробника) =====
@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(get_text(message.from_user.id, "stats_denied"))
        return
    log_button(message.from_user.id, "/stats")
    await message.answer(get_stats())


@router.callback_query(F.data.startswith("menu:"))
async def inline_main_menu(callback: CallbackQuery):
    """Кнопки меню прямо в чаті (inline)."""
    user_id = callback.from_user.id
    action = callback.data.split(":")[1]
    log_button(user_id, f"menu:{action}")
    await callback.answer()

    if action == "metro":
        from handlers.metro import get_lines_keyboard, resolve_map_path
        from aiogram.types import FSInputFile
        text = get_text(user_id, "choose_line")
        map_path = resolve_map_path()
        if map_path:
            await callback.message.answer_photo(
                FSInputFile(map_path), caption=text, reply_markup=get_lines_keyboard()
            )
        else:
            await callback.message.answer(text, reply_markup=get_lines_keyboard())
    elif action == "places":
        from keyboards.menus import places_menu
        await callback.message.answer(
            get_text(user_id, "places_section"),
            reply_markup=places_menu(user_id),
        )
    elif action == "food":
        from handlers.extra import _load
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        from locales import localize_field, get_user_lang
        lang = get_user_lang(user_id)
        data = _load("food.json")
        builder = InlineKeyboardBuilder()
        for cat in data.get("categories", []):
            title = cat.get(lang) or cat.get("uk") or cat["id"]
            builder.button(text=title, callback_data=f"food_cat:{cat['id']}")
        builder.button(text=get_text(user_id, "all_places"), callback_data="food_cat:all")
        builder.adjust(1)
        await callback.message.answer(get_text(user_id, "food_section"), reply_markup=builder.as_markup())
    elif action == "hotels":
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        for stars in range(1, 6):
            builder.button(text="⭐" * stars, callback_data=f"hotel_star:{stars}")
        builder.button(text=get_text(user_id, "all_hotels"), callback_data="hotel_star:0")
        builder.adjust(1)
        await callback.message.answer(get_text(user_id, "choose_hotel_stars"), reply_markup=builder.as_markup())
    elif action == "phrases":
        from handlers.extra import _load
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        lang = get_user_lang(user_id)
        data = _load("phrases.json")
        builder = InlineKeyboardBuilder()
        for cat in data.get("categories", []):
            title = cat.get(lang) or cat.get("uk") or cat["id"]
            builder.button(text=title, callback_data=f"phrase_cat:{cat['id']}")
        builder.adjust(1)
        await callback.message.answer(get_text(user_id, "phrases_section"), reply_markup=builder.as_markup())
    elif action == "updates":
        from handlers.extra import _load
        lang = get_user_lang(user_id)
        data = _load("changelog.json")
        updates = data.get("updates", [])
        lines = [get_text(user_id, "updates_title")]
        for u in updates:
            items = u.get(lang) or u.get("uk") or []
            body = "\n".join(f"• {i}" for i in items)
            lines.append(f"\n📅 <b>{u.get('date','')}</b> · v{u.get('version','')}\n{body}")
        await callback.message.answer("\n".join(lines)[:4000])
    elif action == "alerts":
        await _show_alerts_menu(callback, user_id)
    elif action == "game":
        from handlers.game import start_round
        await start_round(callback.message, user_id)
    elif action == "contacts":
        link = CONTACT_URL or (f"@{CONTACT_USERNAME}" if CONTACT_USERNAME else "—")
        text = (
            get_text(user_id, "contacts_title")
            + "\n\n"
            + get_text(user_id, "contacts_body", extra=get_text(user_id, "contacts_extra"), link=link)
        )
        await callback.message.answer(
            text,
            reply_markup=contacts_keyboard(user_id),
            disable_web_page_preview=True,
        )
