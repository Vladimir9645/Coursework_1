import pytest
import pandas as pd

from src.services import (
    generate_mock_transactions,
    top_5_transactions,
    calc_category_stats,
    calc_cashback_by_category,
    calc_expenses_and_income,
    fetch_currency_rates,
    fetch_sp500_stocks,
)


def test_generate_mock_transactions_structure():
    df = generate_mock_transactions()
    required_cols = {"date", "amount", "category", "description", "type", "card_last4"}
    assert required_cols.issubset(df.columns)
    assert len(df) > 0


def test_top_5_transactions():
    df = generate_mock_transactions()
    result = top_5_transactions(df)
    assert isinstance(result, list)
    assert 0 < len(result) <= 5
    assert "date" in result[0]
    assert "amount" in result[0]


def test_category_stats_top_7_and_rest():
    df = generate_mock_transactions()
    result = calc_category_stats(df)
    assert isinstance(result, list)
    assert 0 < len(result) <= 8
    if len(result) == 8:
        assert any(item["category"] == "Остальное" for item in result)


def test_cashback_calculation():
    df = generate_mock_transactions()
    result = calc_cashback_by_category(df)
    assert isinstance(result, list)
    assert 0 < len(result) <= 3
    for item in result:
        assert "category" in item
        assert "cashback" in item


def test_expenses_and_income():
    df = generate_mock_transactions()
    result = calc_expenses_and_income(df)
    print("expenses:", result["expenses"])
    print("income:", result["income"])
    assert "expenses" in result
    assert "income" in result
    assert result["expenses"] >= 0
    assert result["income"] >= 0



def test_currency_and_stocks_data():
    rates = fetch_currency_rates()
    stocks = fetch_sp500_stocks()
    assert len(rates) > 0
    assert "rate" in rates[0]
    assert "currency" in rates[0]
    assert len(stocks) > 0
    assert "price" in stocks[0]
    assert "stock" in stocks[0]


