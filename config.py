import os
from dotenv import load_dotenv

load_dotenv()

# Токен только в .env — никогда не коммитьте .env в git/архив
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ID разработчиков (могут смотреть /stats)
# Узнать свой ID: @userinfobot
ADMIN_IDS = [
    8655059969,
    7121396037,
    5412830398,
]

# Контакты разработчика (кнопка в меню)
# Текст опису — у locales.py (contacts_extra), щоб працювала локалізація
CONTACT_USERNAME = os.getenv("CONTACT_USERNAME", "XDAS2")
CONTACT_URL = os.getenv(
    "CONTACT_URL",
    f"https://t.me/{CONTACT_USERNAME.lstrip('@')}" if CONTACT_USERNAME else "",
)
