import json
import os
import pytest

import pandas as pd

from src.reports import (
    spending_by_category,
    spending_by_weekday,
    spending_by_workday,
    save_report,
)


@pytest.fixture
def sample_df():
    start_date = pd.Timestamp("2024-09-01")
    end_date = pd.Timestamp("2024-12-31")
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    categories = ["Продукты", "Транспорт", "Одежда", "Развлечения"]
    amounts = [100 + i % 500 for i in range(len(dates))]

    df = pd.DataFrame({
        "date": dates,
        "category": [categories[i % len(categories)] for i in range(len(dates))],
        "amount": amounts,
    })
    return df


@pytest.fixture
def tmp_json_path(tmp_path):
    return tmp_path / "custom_report.json"


# --- Тесты декоратора save_report ---

def test_save_report_default_filename(sample_df, tmp_path):
    import sys
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)

        @save_report()
        def dummy_report(df):
            return df.head(5)

        res = dummy_report(sample_df)
        assert isinstance(res, pd.DataFrame)
        files = [f.name for f in tmp_path.iterdir()]
        assert any(f.startswith("report_dummy_report_") and f.endswith(".json") for f in files)
    finally:
        os.chdir(old_cwd)


def test_save_report_custom_filename(sample_df, tmp_json_path):
    @save_report(str(tmp_json_path))
    def dummy_report(df):
        return df.head(3)

    res = dummy_report(sample_df)
    assert isinstance(res, pd.DataFrame)
    assert tmp_json_path.exists()

    with open(tmp_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, list)
    assert len(data) == 3
    assert "date" in data[0]


# --- Тесты spending_by_category ---

def test_spending_by_category_filters_3_months(sample_df):
    ref_date = "2024-11-15"
    res = spending_by_category(sample_df, category="Транспорт", date=ref_date)

    ref = pd.to_datetime(ref_date)
    start = ref - pd.Timedelta(days=90)

    if not res.empty:
        assert res["date"].between(start, ref).all()


def test_spending_by_category_case_insensitive(sample_df):
    res1 = spending_by_category(sample_df, category="продукты", date="2024-11-15")
    res2 = spending_by_category(sample_df, category="ПРОДУКТЫ", date="2024-11-15")
    assert len(res1) == len(res2)


# --- Тесты spending_by_weekday ---

def test_spending_by_weekday_columns(sample_df):
    res = spending_by_weekday(sample_df, date="2024-11-15")
    expected_cols = {"weekday", "total_amount", "count_transactions"}
    assert set(res.columns) == expected_cols


# --- Тесты spending_by_workday ---

def test_spending_by_workday_columns(sample_df):
    res = spending_by_workday(sample_df, date="2024-11-15")
    expected_cols = {"day_type", "total_amount", "count_transactions"}
    assert set(res.columns) == expected_cols


# --- Интеграционные тесты: факт сохранения файлов ---

def test_spending_by_category_saves_file(sample_df, tmp_path):
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        spending_by_category(sample_df, category="Одежда", date="2024-11-15")
        files = [f.name for f in tmp_path.iterdir()]
        assert any(f.startswith("report_spending_by_category_") and f.endswith(".json") for f in files)
    finally:
        os.chdir(old_cwd)


