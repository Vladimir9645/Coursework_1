import json
from datetime import datetime

from src.external_api import get_currency_rates, get_stock_prices
from src.services import (
    build_cards,
    build_expenses_and_income,
    calc_cashback_by_category,
    calc_category_stats,
    calc_expenses_and_income,
    filter_current_month,
    search_transactions,
    top_5_transactions,
)
from src.utils import (
    get_greeting,
    load_transactions,
    load_user_settings,
)


def main_response(
    input_datetime_str: str,
    query: str | None = None,
    phone: str | None = None,
) -> str:
    requested_at = datetime.strptime(
        input_datetime_str.strip(),
        "%Y-%m-%d %H:%M:%S",
    )
    month_transactions = filter_current_month(
        load_transactions(),
        requested_at,
    )
    transactions = search_transactions(
        month_transactions,
        query=query,
        phone=phone,
    )
    settings = load_user_settings()
    totals = build_expenses_and_income(transactions)

    response = {
        "greeting": get_greeting(requested_at),
        "cards": build_cards(transactions),
        "top_5_transactions": top_5_transactions(transactions),
        "expenses": totals["expenses"],
        "income": totals["income"],
        "expenses_and_income": calc_expenses_and_income(
            transactions
        ),
        "category_stats": calc_category_stats(transactions),
        "cashback_by_category": calc_cashback_by_category(
            transactions
        ),
        "currency_rates": get_currency_rates(
            settings["user_currencies"]
        ),
        "stock_prices": get_stock_prices(
            settings["user_stocks"]
        ),
    }
    return json.dumps(response, ensure_ascii=False, indent=2)


