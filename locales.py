"""
Локалізація бота.

Щоб додати нову мову:
  1. Додай код мови в SUPPORTED_LANGS (напр. "pl")
  2. Скопіюй блок "uk" → новий ключ і переклади рядки
  3. (опційно) REGION_NAMES[lang] = {id: "назва області", ...}
Мова користувача зберігається у data/user_languages.json
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger("bot.locales")

_DATA_DIR = Path(__file__).resolve().parent / "data"
_LANG_FILE = _DATA_DIR / "user_languages.json"

# --- коди мов (порядок у меню) ---
SUPPORTED_LANGS = ("uk", "en")  # далі: "pl", "de", ...
DEFAULT_LANG = "uk"

# Прапорці / підписи для меню вибору мови
LANG_LABELS = {
    "uk": "🇺🇦 Українська",
    "en": "🇬🇧 English",
    # "pl": "🇵🇱 Polski",
}

# Назви областей (id з alerts.com.ua) — для списку «тривога не в Харкові»
REGION_NAMES: dict[str, dict[int, str]] = {
    "uk": {
        1: "Вінницька", 2: "Волинська", 3: "Дніпропетровська", 4: "Донецька",
        5: "Житомирська", 6: "Закарпатська", 7: "Запорізька", 8: "Івано-Франківська",
        9: "Київська", 10: "Кіровоградська", 11: "Луганська", 12: "Львівська",
        13: "Миколаївська", 14: "Одеська", 15: "Полтавська", 16: "Рівненська",
        17: "Сумська", 18: "Тернопільська", 19: "Харківська", 20: "Херсонська",
        21: "Хмельницька", 22: "Черкаська", 23: "Чернівецька", 24: "Чернігівська",
        25: "м. Київ", 26: "АР Крим", 27: "м. Севастополь",
    },
    "en": {
        1: "Vinnytsia", 2: "Volyn", 3: "Dnipropetrovsk", 4: "Donetsk",
        5: "Zhytomyr", 6: "Zakarpattia", 7: "Zaporizhzhia", 8: "Ivano-Frankivsk",
        9: "Kyiv oblast", 10: "Kirovohrad", 11: "Luhansk", 12: "Lviv",
        13: "Mykolaiv", 14: "Odesa", 15: "Poltava", 16: "Rivne",
        17: "Sumy", 18: "Ternopil", 19: "Kharkiv", 20: "Kherson",
        21: "Khmelnytskyi", 22: "Cherkasy", 23: "Chernivtsi", 24: "Chernihiv",
        25: "Kyiv city", 26: "Crimea", 27: "Sevastopol",
    },
}

texts: dict[str, dict[str, str]] = {
    "uk": {
        "start": "Привіт! 👋\nЯ бот-навігатор Харковом.\nОбери, що тебе цікавить:",
        "help": (
            "Я можу допомогти тобі:\n"
            "• Знайти станції метро\n"
            "• Показати цікаві місця\n"
            "• Де поїсти та готелі\n"
            "• Банкомати поруч\n"
            "• Корисні фрази\n"
            "• Сповіщення про тривогу (/alerts)\n"
            "• Перевірити статус тривоги зараз (/status)\n• Гру «Вгадай станцію»\n\n"
            "Команди: /help · /alerts · /status · /start\n\n"
            "Створювач бота: <b>#XDAS2</b>"
        ),
        "main_menu": "Головне меню:",
        "choose_language": "Обери мову / Choose language:",
        "language_changed": "Мову змінено на українську 🇺🇦",
        "back": "⬅️ Назад",

        "metro": "🚇 Метро",
        "places": "📍 Цікаві місця",
        "help_btn": "ℹ️ Допомога",
        "language_btn": "🌐 Language",
        "alerts_btn": "🚨 Тривога",
        "contacts_btn": "📞 Контакти",

        "choose_line": "Обери лінію метро:",
        "choose_station": "Обери станцію:",
        "no_stations": "На цій лінії поки немає станцій.",
        "station_not_found": "Станцію не знайдено",
        "metro_schedule_btn": "🕐 Розклад",

        "places_section": "Цікаві місця міста 📍\nОбери дію:",
        "all_places": "Усі місця",
        "by_category": "За категоріями",
        "places_title": "Визначні місця:",
        "choose_place": "Обери місце:",
        "choose_category": "Обери категорію:",
        "no_places": "Поки немає доданих місць.",
        "place_not_found": "Місце не знайдено",
        "nearby_places": "📍 Місця поруч",
        "nearby_stations": "🚇 Станції поруч",
        "no_nearby": "Поруч поки немає місць",

        "schedule_btn": "🕐 Розклад",
        "schedule_title": "🚇 <b>Розклад метро (найближча година)</b>",
        "schedule_closed": (
            "🚇 <b>Розклад метро</b>\n\n"
            "Зараз метро зачинене.\n"
            "Працює: <b>05:30 – 22:00</b> (час Києва)\n\n"
            "<i>Інтервали можуть змінюватися через енергоситуацію.</i>"
        ),
        "schedule_open": (
            "🚇 <b>Розклад метро (найближча година)</b>\n\n"
            "Поточний інтервал: близько <b>{interval} хв</b>\n"
            "Найближчі поїзди (приблизно):\n<code>{times}</code>\n\n"
            "Працює: 05:30 – 22:00 (час Києва)\n"
            "<i>Дані приблизні. Уточнюйте за офіційними джерелами.</i>"
        ),

        "alerts_status_on": "увімкнені ✅",
        "alerts_status_off": "вимкнені ❌",
        "alerts_info": (
            "Сповіщення про повітряну тривогу зараз <b>{status}</b>\n\n"
            "Бот повідомлятиме, коли починається та закінчується тривога "
            "в Харківській області.\n\n"
            "Натисни «Перевірити зараз», щоб дізнатися поточний статус."
        ),
        "alerts_enabled": "✅ Сповіщення про тривогу <b>увімкнені</b>",
        "alerts_disabled": "❌ Сповіщення про тривогу <b>вимкнені</b>",
        "alerts_on_btn": "Увімкнути",
        "alerts_off_btn": "Вимкнути",
        "alerts_check_btn": "🔄 Перевірити зараз",
        "alert_active": "🚨 Зараз у Харківській області <b>повітряна тривога</b>",
        "alert_clear": "✅ Зараз у Харківській області <b>тривоги немає</b>",
        "alert_start": (
            "🚨 <b>Повітряна тривога в Харківській області!</b>\n"
            "Пройдіть в укриття та стежте за офіційними повідомленнями."
        ),
        "alert_end": "✅ <b>Відбій повітряної тривоги в Харківській області</b>",
        "status_checking": "⏳ Перевіряю статус тривоги…",
        "alert_elsewhere_title": (
            "✅ У <b>Харківській області</b> тривоги <b>немає</b>.\n\n"
            "⚠️ Але зараз повітряна тривога в інших регіонах:"
        ),
        "alert_elsewhere_footer": (
            "\n\nКарта нижче — щоб було зрозуміло: тривога є в країні, "
            "але <b>не в Харкові / Харківській області</b>.\n"
            "Джерело: <a href=\"https://alerts.com.ua\">alerts.com.ua</a>"
        ),
        "alert_none_anywhere": (
            "✅ Зараз у Харківській області <b>тривоги немає</b>.\n"
            "В інших регіонах України активних тривог теж не виявлено."
        ),
        "alert_map_caption": "",
        "alert_regions_list_item": "• {name}",

        "food_btn": "🍽️ Де поїсти",
        "hotels_btn": "🏨 Готелі",
        "atms_btn": "💳 Банкомати",
        "phrases_btn": "💬 Фрази",
        "food_section": "Де поїсти 🍽️\nОбери заклад:",
        "hotels_section": "Готелі 🏨\nОбери готель:",
        "phrases_section": "Корисні фрази 💬\nОбери категорію:",
        "nearby_atms": "Банкомати поруч",
        "atms_hint": (
            "💳 Банкомати показано на картках станцій метро та цікавих місць "
            "(кнопка або блок «Банкомати поруч»).\n\n"
            "Також банкомати вказані біля закладів харчування та готелів."
        ),
        "no_atms_nearby": "Поруч банкоматів не знайдено",
        "updates_btn": "📰 Оновлення",
        "updates_title": "📰 <b>Історія оновлень бота</b>\n",
        "updates_empty": "Поки немає записів про оновлення.",
        "nearby_food": "🍽️ Де поїсти поруч",
        "nearby_hotels": "🏨 Готелі поруч",
        "choose_hotel_stars": "Обери кількість зірок готелю:",
        "all_hotels": "Усі готелі поруч",
        "no_food_nearby": "Поруч закладів харчування не знайдено",
        "no_hotels_nearby": "Поруч готелів не знайдено",
        "station_services": "🏪 Що поруч",
        "game_btn": "🎮 Гра",
        "game_section": "🎮 <b>Вгадай станцію метро</b>\nДивись фото і обери правильну назву:",
        "game_correct": "✅ Правильно! Це <b>{name}</b>",
        "game_wrong": "❌ Ні. Правильна відповідь: <b>{name}</b>",
        "game_again": "Ще раз",
        "game_no_photos": "Немає фото станцій для гри.",
        "game_score": "Рахунок: <b>{score}</b> правильних підряд",

        "contacts_title": "📞 <b>Контакти</b>",
        "contacts_extra": "Створювач бота: <b>#XDAS2</b>\nПишіть з питань роботи бота або пропозицій.",
        "contacts_body": "{extra}\n\nTelegram: {link}",
        "contacts_open": "Написати в Telegram",
        "stats_denied": "⛔ Ця команда доступна лише розробникам.",
        "no_access": "⛔ Немає доступу.",
        "google_maps": "Google Maps",
        "map_link": "карта",
        "dash": "—",
    },

    "en": {
        "start": "Hi! 👋\nI'm a Kharkiv city navigator bot.\nChoose what you're interested in:",
        "help": (
            "I can help you:\n"
            "• Find metro stations\n"
            "• Show interesting places\n"
            "• Food and hotels\n"
            "• Nearby ATMs\n"
            "• Useful phrases\n"
            "• Air raid alerts (/alerts)\n"
            "• Check current alert status (/status)\n• «Guess the station» game\n\n"
            "Commands: /help · /alerts · /status · /start\n\n"
            "Bot creator: <b>#XDAS2</b>"
        ),
        "main_menu": "Main menu:",
        "choose_language": "Обери мову / Choose language:",
        "language_changed": "Language changed to English 🇬🇧",
        "back": "⬅️ Back",

        "metro": "🚇 Metro",
        "places": "📍 Places",
        "help_btn": "ℹ️ Help",
        "language_btn": "🌐 Language",
        "alerts_btn": "🚨 Alerts",
        "contacts_btn": "📞 Contacts",

        "choose_line": "Choose metro line:",
        "choose_station": "Choose a station:",
        "no_stations": "There are no stations on this line yet.",
        "station_not_found": "Station not found",
        "metro_schedule_btn": "🕐 Schedule",

        "places_section": "Interesting places 📍\nChoose an action:",
        "all_places": "All places",
        "by_category": "By category",
        "places_title": "Attractions:",
        "choose_place": "Choose a place:",
        "choose_category": "Choose a category:",
        "no_places": "No places added yet.",
        "place_not_found": "Place not found",
        "nearby_places": "📍 Nearby places",
        "nearby_stations": "🚇 Nearby stations",
        "no_nearby": "No nearby places yet",

        "schedule_btn": "🕐 Schedule",
        "schedule_title": "🚇 <b>Metro schedule (next hour)</b>",
        "schedule_closed": (
            "🚇 <b>Metro schedule</b>\n\n"
            "Metro is currently closed.\n"
            "Working hours: <b>05:30 – 22:00</b> (Kyiv time)\n\n"
            "<i>Intervals may change due to the energy situation.</i>"
        ),
        "schedule_open": (
            "🚇 <b>Metro schedule (next hour)</b>\n\n"
            "Current interval: about <b>{interval} min</b>\n"
            "Next trains (approx.):\n<code>{times}</code>\n\n"
            "Working hours: 05:30 – 22:00 (Kyiv time)\n"
            "<i>Approximate data. Check official sources.</i>"
        ),

        "alerts_status_on": "enabled ✅",
        "alerts_status_off": "disabled ❌",
        "alerts_info": (
            "Air raid alert notifications are currently <b>{status}</b>\n\n"
            "The bot will notify you when an alert starts or ends in Kharkiv oblast.\n\n"
            "Tap «Check now» to see the current status."
        ),
        "alerts_enabled": "✅ Alert notifications <b>enabled</b>",
        "alerts_disabled": "❌ Alert notifications <b>disabled</b>",
        "alerts_on_btn": "Enable",
        "alerts_off_btn": "Disable",
        "alerts_check_btn": "🔄 Check now",
        "alert_active": "🚨 There is currently an <b>air raid alert</b> in Kharkiv oblast",
        "alert_clear": "✅ There is currently <b>no alert</b> in Kharkiv oblast",
        "alert_start": (
            "🚨 <b>Air raid alert in Kharkiv oblast!</b>\n"
            "Go to a shelter and follow official updates."
        ),
        "alert_end": "✅ <b>All clear in Kharkiv oblast</b>",
        "status_checking": "⏳ Checking alert status…",
        "alert_elsewhere_title": (
            "✅ There is <b>no alert</b> in <b>Kharkiv oblast</b>.\n\n"
            "⚠️ But air raid alerts are active in other regions:"
        ),
        "alert_elsewhere_footer": (
            "\n\nThe map below helps you see: there is an alert in the country, "
            "but <b>not in Kharkiv / Kharkiv oblast</b>.\n"
            "Source: <a href=\"https://alerts.com.ua\">alerts.com.ua</a>"
        ),
        "alert_none_anywhere": (
            "✅ There is currently <b>no alert</b> in Kharkiv oblast.\n"
            "No active alerts detected in other regions of Ukraine either."
        ),
        "alert_map_caption": "",
        "alert_regions_list_item": "• {name}",

        "food_btn": "🍽️ Food",
        "hotels_btn": "🏨 Hotels",
        "atms_btn": "💳 ATMs",
        "phrases_btn": "💬 Phrases",
        "food_section": "Where to eat 🍽️\nChoose a place:",
        "hotels_section": "Hotels 🏨\nChoose a hotel:",
        "phrases_section": "Useful phrases 💬\nChoose a category:",
        "nearby_atms": "ATMs nearby",
        "atms_hint": (
            "💳 ATMs are shown on metro station and place cards («ATMs nearby»).\n\n"
            "Also listed for restaurants and hotels."
        ),
        "no_atms_nearby": "No ATMs found nearby",
        "updates_btn": "📰 Updates",
        "updates_title": "📰 <b>Bot update history</b>\n",
        "updates_empty": "No update records yet.",
        "nearby_food": "🍽️ Food nearby",
        "nearby_hotels": "🏨 Hotels nearby",
        "choose_hotel_stars": "Choose hotel star rating:",
        "all_hotels": "All nearby hotels",
        "no_food_nearby": "No food places nearby",
        "no_hotels_nearby": "No hotels nearby",
        "station_services": "🏪 Nearby services",
        "game_btn": "🎮 Game",
        "game_section": "🎮 <b>Guess the metro station</b>\nLook at the photo and pick the right name:",
        "game_correct": "✅ Correct! It's <b>{name}</b>",
        "game_wrong": "❌ No. The answer is <b>{name}</b>",
        "game_again": "Play again",
        "game_no_photos": "No station photos for the game.",
        "game_score": "Score: <b>{score}</b> correct in a row",

        "contacts_title": "📞 <b>Contacts</b>",
        "contacts_extra": "Bot creator: <b>#XDAS2</b>\nWrite about the bot or suggestions.",
        "contacts_body": "{extra}\n\nTelegram: {link}",
        "contacts_open": "Message on Telegram",
        "stats_denied": "⛔ This command is for developers only.",
        "no_access": "⛔ Access denied.",
        "google_maps": "Google Maps",
        "map_link": "map",
        "dash": "—",
    },
}

# Перевірка: усі ключі uk мають бути в інших мовах (попередження в лог при імпорті)
def _validate_keys() -> None:
    base = set(texts.get(DEFAULT_LANG, {}))
    for lang, data in texts.items():
        missing = base - set(data)
        if missing:
            logger.warning("locale %s missing keys: %s", lang, sorted(missing)[:10])


_validate_keys()

user_languages: dict[int, str] = {}


def _load_languages() -> None:
    global user_languages
    try:
        if not _LANG_FILE.exists():
            return
        raw = json.loads(_LANG_FILE.read_text(encoding="utf-8"))
        user_languages = {
            int(k): v for k, v in raw.items() if v in texts
        }
        logger.info("loaded languages for %s users", len(user_languages))
    except Exception as e:
        logger.warning("failed to load languages: %s", e)
        user_languages = {}


def _save_languages() -> None:
    try:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        payload = {str(k): v for k, v in user_languages.items()}
        _LANG_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning("failed to save languages: %s", e)


_load_languages()


def get_user_lang(user_id: int) -> str:
    return user_languages.get(user_id, DEFAULT_LANG)


def set_language(user_id: int, lang: str) -> None:
    if lang in texts:
        user_languages[user_id] = lang
        _save_languages()


def t(lang: str, key: str, **kwargs) -> str:
    """Текст за кодом мови (без user_id). Зручно для фонових задач."""
    pack = texts.get(lang) or texts[DEFAULT_LANG]
    text = pack.get(key) or texts[DEFAULT_LANG].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def get_text(user_id: int, key: str, **kwargs) -> str:
    return t(get_user_lang(user_id), key, **kwargs)


def get_all_texts(key: str) -> list[str]:
    """Усі переклади ключа — для фільтрів кнопок."""
    return [lang_data[key] for lang_data in texts.values() if key in lang_data]


def localize_field(value, lang: str, default: str = "") -> str:
    """Локалізація поля з JSON (uk / en / ru …)."""
    if isinstance(value, dict):
        return (
            value.get(lang)
            or value.get("uk")
            or value.get("ru")
            or value.get("en")
            or default
        )
    return value or default


def region_name(lang: str, region_id: int, fallback: str = "") -> str:
    names = REGION_NAMES.get(lang) or REGION_NAMES.get(DEFAULT_LANG, {})
    return names.get(region_id) or fallback or str(region_id)


def language_changed_key(lang: str) -> str:
    """Після вибору мови — ключ language_changed (один на всі мови)."""
    return "language_changed"
