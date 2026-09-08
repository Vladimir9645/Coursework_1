import pytest
from datetime import datetime
from src.utils import get_greeting, format_datetime

@pytest.mark.parametrize("hour,expected", [
    (5, "Доброй ночи"),      # было "Доброе утро"
    (11, "Доброе утро"),
    (12, "Добрый день"),
    (16, "Добрый день"),
    (17, "Добрый день"),     # было "Добрый вечер"
    (22, "Добрый вечер"),
    (23, "Доброй ночи"),
    (4, "Доброй ночи"),
])

def test_get_greeting(hour, expected):
    """Проверяет корректность приветствия в зависимости от часа."""
    dt = datetime(2024, 10, 1, hour, 0, 0)
    assert get_greeting(dt) == expected

def test_format_datetime():
    """Проверяет форматирование datetime в строку нужного формата."""
    dt = datetime(2024, 10, 1, 15, 30, 0)
    assert format_datetime(dt) == "2024-10-01 15:30:00"
