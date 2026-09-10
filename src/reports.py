import json
import logging
import os
from datetime import timedelta
from typing import Any, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Вспомогательная функция: приведение объектов к JSON-совместимому виду
# -----------------------------------------------------------------------------


def _to_json_compatible(obj: Any) -> Any:
    """
    Рекурсивно приводит объекты к JSON-сериализуемым типам.
    Особенно важно для pd.Timestamp, pd.NaT, numpy типов и т.п.
    """
    if isinstance(obj, pd.Timestamp):
        # Конвертируем Timestamp в ISO-строку
        return obj.isoformat()
    if isinstance(obj, pd.Timedelta):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _to_json_compatible(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_json_compatible(i) for i in obj]
    if isinstance(obj, tuple):
        return [_to_json_compatible(i) for i in obj]
    # Для остальных типов возвращаем как есть — пусть json.dump решает
    return obj


# -----------------------------------------------------------------------------
# Декоратор для сохранения результата отчёта в файл
# -----------------------------------------------------------------------------


def save_report(filename: Optional[str] = None):
    """Декоратор для функций-отчётов. Сохраняет возвращаемое значение (DataFrame или dict)
    в JSON-файл.
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)

            # Формируем имя файла
            if filename is None:
                import datetime

                base_name = f"report_{func.__name__}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                out_path = base_name
            else:
                out_path = filename

            # Нормализуем результат к dict/list для JSON
            if isinstance(result, pd.DataFrame):
                # Сначала конвертируем DataFrame в список словарей
                data_to_save = result.to_dict(orient="records")
                # Затем приводим все значения к JSON-совместимым (особенно даты)
                data_to_save = _to_json_compatible(data_to_save)
            elif isinstance(result, dict):
                data_to_save = _to_json_compatible(result)
            elif isinstance(result, list):
                data_to_save = _to_json_compatible(result)
            else:
                logger.warning(
                    "Результат отчёта не в поддерживаемом формате. Сохраняем str(result)."
                )
                data_to_save = str(result)

            try:
                dir_name = os.path.dirname(out_path)
                if dir_name and not os.path.exists(dir_name):
                    os.makedirs(dir_name, exist_ok=True)

                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(data_to_save, f, ensure_ascii=False, indent=2)
                logger.info("Отчёт сохранён в: %s", out_path)
            except Exception as e:
                logger.error("Не удалось сохранить отчёт в %s: %s", out_path, e)
                raise

            return result

        return wrapper

    return decorator


# -----------------------------------------------------------------------------
# Функции отчётов (примерная реализация — оставь свою логику, она не меняется)
# -----------------------------------------------------------------------------


@save_report()
def spending_by_category(df: pd.DataFrame, category: str, date: str) -> pd.DataFrame:
    """
    Возвращает траты по конкретной категории за последние 3 месяца от указанной даты.
    Дата передаётся в формате YYYY-MM-DD.
    """
    ref_date = pd.to_datetime(date)
    start_date = ref_date - pd.Timedelta(days=90)

    # Фильтрация по диапазону дат
    mask = (df["date"] >= start_date) & (df["date"] <= ref_date)
    filtered = df.loc[mask].copy()

    # Фильтр по категории (case-insensitive)
    filtered["category_lower"] = filtered["category"].str.lower()
    category_lower = category.lower()
    filtered = filtered[filtered["category_lower"] == category_lower]
    filtered.drop(columns=["category_lower"], inplace=True, errors="ignore")

    return filtered


@save_report()
def spending_by_weekday(df: pd.DataFrame, date: str) -> pd.DataFrame:
    """
    Траты, сгруппированные по дням недели (0=Пн, 6=Вс) за последние 3 месяца.
    Возвращает DataFrame с колонками: weekday, total_amount, count_transactions.
    """
    ref_date = pd.to_datetime(date)
    start_date = ref_date - pd.Timedelta(days=90)

    mask = (df["date"] >= start_date) & (df["date"] <= ref_date)
    filtered = df.loc[mask].copy()

    filtered["weekday"] = filtered["date"].dt.weekday

    agg = filtered.groupby("weekday", as_index=False).agg(
        total_amount=("amount", "sum"), count_transactions=("amount", "count")
    )

    return agg


@save_report()
def spending_by_workday(df: pd.DataFrame, date: str) -> pd.DataFrame:
    """
    Траты по типу дня: рабочий/выходной за последние 3 месяца.
    Возвращает DataFrame: day_type ('workday' или 'weekend'), total_amount, count_transactions.
    """
    ref_date = pd.to_datetime(date)
    start_date = ref_date - pd.Timedelta(days=90)

    mask = (df["date"] >= start_date) & (df["date"] <= ref_date)
    filtered = df.loc[mask].copy()

    filtered["day_type"] = filtered["date"].dt.weekday.apply(
        lambda x: "weekend" if x >= 5 else "workday"
    )

    agg = filtered.groupby("day_type", as_index=False).agg(
        total_amount=("amount", "sum"), count_transactions=("amount", "count")
    )

    return agg

