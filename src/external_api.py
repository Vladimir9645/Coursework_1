import logging

import requests


logger = logging.getLogger(__name__)


def get_currency_rates(currencies: list[str]) -> list[dict]:
    try:
        response = requests.get(
            "https://open.er-api.com/v6/latest/RUB",
            timeout=10,
        )
        response.raise_for_status()
        rates = response.json().get("rates", {})
    except (requests.RequestException, ValueError) as error:
        logger.error("Не удалось получить курсы валют: %s", error)
        return [
            {"currency": currency, "rate": None}
            for currency in currencies
        ]

    result = []
    for currency in currencies:
        api_rate = rates.get(currency)
        rate = round(1 / api_rate, 2) if api_rate else None
        result.append({"currency": currency, "rate": rate})
    return result


def get_stock_prices(stocks: list[str]) -> list[dict]:
    result = []

    for stock in stocks:
        try:
            response = requests.get(
                (
                    "https://query1.finance.yahoo.com/"
                    f"v8/finance/chart/{stock}"
                ),
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10,
            )
            response.raise_for_status()
            chart = response.json()["chart"]["result"][0]
            price = float(chart["meta"]["regularMarketPrice"])
        except (
            requests.RequestException,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
        ) as error:
            logger.error(
                "Не удалось получить цену %s: %s",
                stock,
                error,
            )
            price = None

        result.append({"stock": stock, "price": price})

    return result