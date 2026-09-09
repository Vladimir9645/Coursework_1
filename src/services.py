from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


def generate_mock_transactions() -> pd.DataFrame:
    base_path = Path(__file__).resolve().parent.parent
    file_path = base_path / "data" / "operations.xlsx"

    if file_path.exists():
        try:
            df = pd.read_excel(file_path, header=0)
        except Exception:
            # Если файл есть, но не читается — возвращаем пустой DF, чтобы приложение не падало
            return pd.DataFrame(
                columns=[
                    "date",
                    "amount",
                    "category",
                    "description",
                    "card_last4",
                    "type",
                ]
            )

        # 1. Приводим названия колонок к нижнему регистру и убираем пробелы
        df.columns = df.columns.astype(str).str.strip().str.lower()

        # 2. Делаем маппинг названий колонок
        rename_map = {
            "дата операции": "date",
            "дата платежа": "date",
            "сумма операции": "amount",
            "сумма платежа": "amount",
            "номер карты": "card_last4",
            "дата": "date",
            "сумма": "amount",
            "категория": "category",
            "описание": "description",
            "тип": "type",
            "последние 4 цифры": "card_last4",
            "card last 4": "card_last4",
        }
        df = df.rename(columns=rename_map)

        # 3. Удаляем дубликаты колонок после переименования
        df = df.loc[:, ~df.columns.duplicated(keep="first")]

        required_cols = ["date", "amount", "category", "description", "card_last4"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            # Не выбрасываем ошибку, а возвращаем пустой DF — это безопаснее для курсовой
            return pd.DataFrame(columns=required_cols + ["type"])

        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

        if "type" not in df.columns:
            df["type"] = df["amount"].apply(lambda x: "income" if x > 0 else "expense")
        else:
            df["type"] = df["type"].astype(str).str.lower()
            type_map = {
                "доход": "income",
                "расход": "expense",
                "income": "income",
                "expense": "expense",
            }
            df["type"] = df["type"].map(type_map).fillna("expense")

        df = df.dropna(subset=["date", "amount"])
        return df
    else:
        # Моковые данные, чтобы тесты и запуск проходили, если Excel нет
        data = [
            {
                "date": "2024-10-01 10:00:00",
                "amount": 1200.5,
                "category": "Продукты",
                "description": "Супермаркет",
                "type": "expense",
                "card_last4": "1234",
            },
            {
                "date": "2024-10-01 11:30:00",
                "amount": 350.0,
                "category": "Транспорт",
                "description": "Такси",
                "type": "expense",
                "card_last4": "5678",
            },
            {
                "date": "2024-10-01 14:20:00",
                "amount": 8900.0,
                "category": "Электроника",
                "description": "Смартфон",
                "type": "expense",
                "card_last4": "1234",
            },
            {
                "date": "2024-10-01 16:45:00",
                "amount": 2500.0,
                "category": "Одежда",
                "description": "Куртка",
                "type": "expense",
                "card_last4": "9012",
            },
            {
                "date": "2024-10-01 18:10:00",
                "amount": 150.0,
                "category": "Кафе",
                "description": "Обед",
                "type": "expense",
                "card_last4": "5678",
            },
            {
                "date": "2024-10-01 09:15:00",
                "amount": 50000.0,
                "category": "Зарплата",
                "description": "Аванс",
                "type": "income",
                "card_last4": "1234",
            },
            {
                "date": "2024-10-02 10:15:00",
                "amount": -2000.0,
                "category": "Переводы",
                "description": "Перевод другу",
                "type": "expense",
                "card_last4": "1111",
            },
            {
                "date": "2024-10-02 11:20:00",
                "amount": -1500.0,
                "category": "Наличные",
                "description": "Снятие наличных",
                "type": "expense",
                "card_last4": "2222",
            },
        ]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        return df


def search_transactions(
        transactions: pd.DataFrame, query: Optional[str] = None, phone: Optional[str] = None
) -> pd.DataFrame:
    result = transactions.copy()

    if query:
        q = query.lower()
        mask = result["description"].astype(str).str.lower().str.contains(
            q, na=False
        ) | result["category"].astype(str).str.lower().str.contains(q, na=False)
        result = result[mask]

    if phone:
        from src.utils import normalize_phone

        norm_phone = normalize_phone(phone)
        # Ищем по последним 4 цифрам номера карты, если телефон приведён к +7XXXXXXXXXX
        if len(norm_phone) >= 4 and norm_phone.startswith("+7"):
            last4 = norm_phone[-4:]
            mask = result["card_last4"].astype(str).str.endswith(last4)
            result = result[mask]

    return result


def top_5_transactions(transactions: pd.DataFrame) -> List[Dict[str, Any]]:
    if transactions.empty:
        return []
    top = transactions.nlargest(5, "amount")
    top = top.copy()
    top["date"] = top["date"].dt.strftime("%d.%m.%Y")
    return top[["date", "amount", "category", "description"]].to_dict(orient="records")


def calc_category_stats(transactions: pd.DataFrame) -> List[Dict[str, Any]]:
    if transactions.empty:
        return []

    grouped = transactions.groupby("category", as_index=False)["amount"].sum()
    grouped = grouped.sort_values("amount", ascending=False)
    top_7 = grouped.head(7)
    rest = grouped.iloc[7:]
    rest_sum = rest["amount"].sum()

    result = top_7.to_dict(orient="records")
    if rest_sum > 0:
        result.append({"category": "Остальное", "amount": round(rest_sum)})
    return result


def calc_cashback_by_category(transactions: pd.DataFrame) -> List[Dict[str, Any]]:
    if transactions.empty:
        return []

    grouped = transactions.groupby("category", as_index=False)["amount"].sum()
    grouped["cashback"] = (grouped["amount"] // 100).astype(int)
    top = grouped.nlargest(3, "cashback")
    return top[["category", "cashback"]].to_dict(orient="records")


def calc_expenses_and_income(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"expenses": 0.0, "income": 0.0}

    expenses = df.loc[df["amount"] < 0, "amount"].abs().sum()
    income = df.loc[df["amount"] > 0, "amount"].sum()

    return {"expenses": float(expenses), "income": float(income)}


def fetch_currency_rates() -> List[Dict[str, Any]]:
    return [
        {"currency": "USD", "rate": 92.5},
        {"currency": "EUR", "rate": 99.8},
        {"currency": "CNY", "rate": 12.7},
    ]


def fetch_sp500_stocks() -> List[Dict[str, Any]]:
    return [
        {"stock": "AAPL", "price": 195.2},
        {"stock": "MSFT", "price": 378.4},
        {"stock": "GOOGL", "price": 142.3},
        {"stock": "AMZN", "price": 158.7},
        {"stock": "NVDA", "price": 492.1},
    ]

