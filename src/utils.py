import re
from datetime import datetime


def get_greeting(dt: datetime) -> str:
    hour = dt.hour
    # 06:00–11:59 — «Доброе утро»
    if 6 <= hour <= 11:
        return "Доброе утро"
    # 12:00–17:59 — «Добрый день»
    elif 12 <= hour <= 17:
        return "Добрый день"
    # 18:00–22:59 — «Добрый вечер»
    elif 18 <= hour <= 22:
        return "Добрый вечер"
    # остальное (23:00–05:59) — «Доброй ночи»
    else:
        return "Доброй ночи"


def normalize_phone(phone: str) -> str:
    """
    Приводит телефон к формату +7XXXXXXXXXX.
    Поддерживает форматы: +7 (900) 000-00-00, 89000000000 и т.п.
    Если формат не удаётся привести — возвращает исходную строку.
    """
    if not phone:
        return phone

    digits = re.sub(r"\D", "", phone)

    # Если начинается с 8 и длина 11 — меняем на 7
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]

    # Если начинается с 7 и длина 11 — добавляем плюс
    if digits.startswith("7") and len(digits) == 11:
        return f"+{digits}"

    return phone  # Если формат неверен — возвращаем как есть


def format_datetime(dt: datetime | None = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)
