import json
from datetime import datetime
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
OPERATIONS_PATH = BASE_DIR / "data" / "operations.xlsx"
SETTINGS_PATH = BASE_DIR / "data" / "user_settings.json"

RENAME_MAP = {
    "Дата операции": "date",
    "Сумма платежа": "amount",
    "Номер карты": "card_last4",
    "Категория": "category",
    "Описание": "description",
    "Кэшбэк": "cashback",
}


def get_greeting(dt: datetime) -> str:
    hour = dt.hour
    if 6 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 18:
        return "Добрый день"
    if 18 <= hour < 23:
        return "Добрый вечер"
    return "Доброй ночи"


def format_datetime(
        dt: datetime | None = None,
        fmt: str = "%Y-%m-%d %H:%M:%S",
) -> str:
    return (dt or datetime.now()).strftime(fmt)


def load_transactions(path: Path = OPERATIONS_PATH) -> pd.DataFrame:
    df = pd.read_excel(path, engine="openpyxl")
    df = df.rename(columns=RENAME_MAP)

    required = {
        "date",
        "amount",
        "card_last4",
        "category",
        "description",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"В Excel отсутствуют колонки: {sorted(missing)}")

    df["date"] = pd.to_datetime(
        df["date"],
        format="%d.%m.%Y %H:%M:%S",
        errors="coerce",
    )
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    if "cashback" not in df.columns:
        df["cashback"] = 0.0
    else:
        df["cashback"] = pd.to_numeric(
            df["cashback"],
            errors="coerce",
        ).fillna(0)
    df["card_last4"] = (
        df["card_last4"]
        .astype(str)
        .str.extract(r"(\d{4})$", expand=False)
    )
    df["type"] = df["amount"].apply(
        lambda amount: "income" if amount > 0 else "expense"
    )

    return df.dropna(subset=["date", "amount"])


def load_user_settings(path: Path = SETTINGS_PATH) -> dict:
    with path.open(encoding="utf-8") as file:
        settings = json.load(file)

    return {
        "user_currencies": settings.get("user_currencies", []),
        "user_stocks": settings.get("user_stocks", []),
    }
