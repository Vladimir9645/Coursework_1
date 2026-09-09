import json
from datetime import datetime
from typing import Any, Optional

from src.services import (
    calc_cashback_by_category,
    calc_category_stats,
    calc_expenses_and_income,
    fetch_currency_rates,
    fetch_sp500_stocks,
    generate_mock_transactions,
    search_transactions,
    top_5_transactions,
)
from src.utils import get_greeting


def main_response(
    input_datetime_str: str, query: Optional[str] = None, phone: Optional[str] = None
) -> str:
    cleaned = input_datetime_str.strip()
    try:
        dt = datetime.strptime(cleaned, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return json.dumps({"error": "Invalid datetime format. Use YYYY-MM-DD HH:MM:SS"})

    greeting = get_greeting(dt)
    transactions = generate_mock_transactions()

    filtered = search_transactions(transactions, query, phone)

    cards = filtered["card_last4"].drop_duplicates().tolist()
    cards_data = [{"card_last4": c} for c in cards]

    response = {
        "greeting": greeting,
        "cards": cards_data,
        "top_5_transactions": top_5_transactions(filtered),
        "currency_rates": fetch_currency_rates(),
        "stock_prices": fetch_sp500_stocks(),
        "expenses_and_income": calc_expenses_and_income(filtered),
        "category_stats": calc_category_stats(filtered),
        "cashback_by_category": calc_cashback_by_category(filtered),
    }

    return json.dumps(response, ensure_ascii=False, indent=2)

