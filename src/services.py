import re
from datetime import datetime
from idlelib import query

import pandas as pd
import phone
import result

from src.external_api import get_currency_rates, get_stock_prices
from src.utils import load_transactions, load_user_settings


SPECIAL_CATEGORIES = {"Переводы", "Наличные"}
PHONE_PATTERN = re.compile(
    r"(?:\+7|8)[\s(]*\d{3}[)\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}"
)


def filter_current_month(
    df: pd.DataFrame,
    requested_at: datetime,
) -> pd.DataFrame:
    period_start = requested_at.replace(
        day=1,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )
    return df.loc[
        (df["date"] >= period_start)
        & (df["date"] <= requested_at)
    ].copy()


def build_cards(df: pd.DataFrame) -> list[dict]:
    expenses = df.loc[
        (df["amount"] < 0) & df["card_last4"].notna()
    ].copy()
    expenses["spent"] = expenses["amount"].abs()

    grouped = expenses.groupby("card_last4", as_index=False).agg(
        total_spent=("spent", "sum"),
    )

    return [
        {
            "last_digits": str(row.card_last4),
            "total_spent": round(float(row.total_spent), 2),
            "cashback": round(float(row.total_spent) / 100, 2),
        }
        for row in grouped.itertuples(index=False)
    ]


def top_5_transactions(df: pd.DataFrame) -> list[dict]:
    top = (
        df.assign(sort_amount=df["amount"].abs())
        .nlargest(5, "sort_amount")
        .copy()
    )

    return [
        {
            "date": row.date.strftime("%d.%m.%Y"),
            "amount": round(abs(float(row.amount)), 2),
            "category": str(row.category),
            "description": str(row.description),
        }
        for row in top.itertuples(index=False)
    ]


def _category_items(df: pd.DataFrame) -> list[dict]:
    grouped = (
        df.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )
    return [
        {"category": str(category), "amount": round(float(amount))}
        for category, amount in grouped.items()
    ]


def build_expenses_and_income(df: pd.DataFrame) -> dict:
    expenses = df.loc[df["amount"] < 0].copy()
    expenses["amount"] = expenses["amount"].abs()

    transfers_and_cash = expenses.loc[
        expenses["category"].isin(SPECIAL_CATEGORIES)
    ]
    ordinary_expenses = expenses.loc[
        ~expenses["category"].isin(SPECIAL_CATEGORIES)
    ]

    grouped = (
        ordinary_expenses.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )
    main = [
        {"category": str(category), "amount": round(float(amount))}
        for category, amount in grouped.head(7).items()
    ]
    other_amount = grouped.iloc[7:].sum()
    if other_amount > 0:
        main.append(
            {
                "category": "Остальное",
                "amount": round(float(other_amount)),
            }
        )

    income = df.loc[df["amount"] > 0].copy()

    return {
        "expenses": {
            "total_amount": round(float(expenses["amount"].sum())),
            "main": main,
            "transfers_and_cash": _category_items(
                transfers_and_cash
            ),
        },
        "income": {
            "total_amount": round(float(income["amount"].sum())),
            "main": _category_items(income),
        },
    }


def calc_cashback_by_category(df: pd.DataFrame) -> list[dict]:
    expenses = df.loc[df["amount"] < 0].copy()
    expenses["cashback"] = expenses["amount"].abs() / 100

    grouped = (
        expenses.groupby("category")["cashback"]
        .sum()
        .nlargest(3)
    )
    return [
        {
            "category": str(category),
            "cashback": round(float(cashback), 2),
        }
        for category, cashback in grouped.items()
    ]


def simple_search(
    df: pd.DataFrame,
    query: str,
) -> pd.DataFrame:
    escaped_query = re.escape(query)
    mask = (
        df["description"].astype(str).str.contains(
            escaped_query,
            case=False,
            regex=True,
            na=False,
        )
        | df["category"].astype(str).str.contains(
            escaped_query,
            case=False,
            regex=True,
            na=False,
        )
    )
    return df.loc[mask].copy()


def search_phone_transactions(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["description"].astype(str).apply(
        lambda value: bool(PHONE_PATTERN.search(value))
    )
    return df.loc[mask].copy()

def generate_mock_transactions() -> pd.DataFrame:
    return load_transactions()
def calc_category_stats(df: pd.DataFrame) -> list[dict]:
    return build_expenses_and_income(df)["expenses"]["main"]
def calc_expenses_and_income(df: pd.DataFrame) -> dict:
    return {
        "expenses": round(
            float(df.loc[df["amount"] < 0, "amount"].abs().sum()),
            2,
        ),
        "income": round(
            float(df.loc[df["amount"] > 0, "amount"].sum()),
            2,
        ),
    }

def fetch_currency_rates() -> list[dict]:
    settings = load_user_settings()
    return get_currency_rates(settings["user_currencies"])
def fetch_sp500_stocks() -> list[dict]:
    settings = load_user_settings()
    return get_stock_prices(settings["user_stocks"])
def search_transactions(
    df: pd.DataFrame,
    query: str | None = None,
    phone: str | None = None,
) -> pd.DataFrame:
    result = df.copy()

    if query:
        result = simple_search(result, query)

    if phone:
        target_digits = re.sub(r"\D", "", phone)[-10:]
        if target_digits:
            phone_mask = result["description"].astype(str).apply(
                lambda description: target_digits
                in re.sub(r"\D", "", description)
            )
            result = result.loc[phone_mask].copy()

    return result
