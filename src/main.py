"""
main.py — демонстрация всех возможностей проекта.
"""

import json

from src.services import (
    analyze_cashback_categories,
    investment_bank,
    search_phone_numbers,
    search_private_transfers,
    simple_search,
)
from src.views import generate_events_page_data, generate_main_page_data


# === Пример входной даты ===
input_date_str = "2025-05-15 12:00:00"

print("== Главная страница ==")
main_result = generate_main_page_data(input_date_str)
print(json.dumps(main_result, ensure_ascii=False, indent=2))

print("== Страница событий (месяц) ==")
events_result = generate_events_page_data(input_date_str, period="M")
print(json.dumps(events_result, ensure_ascii=False, indent=2))

# === Пример транзакций ===
transactions = [
    {
        "Дата операции": "2025-05-01",
        "Категория": "Еда",
        "Сумма списания": 120.0,
        "Сумма операции": 120.0,
        "Описание": "Магазин Перекресток +7 999 123-45-67",
    },
    {
        "Дата операции": "2025-05-02",
        "Категория": "Переводы",
        "Сумма списания": 200.0,
        "Сумма операции": 200.0,
        "Описание": "Иванов И.",
    },
]

print("== Кешбэк по категориям ==")
print(analyze_cashback_categories(transactions, 2025, 5))

print("== Инвесткопилка ==")
print(investment_bank("2025-05", transactions))

print('== Поиск по ключевому слову ("перекресток") ==')
print(simple_search(transactions, "перекресток"))

print("== Поиск номеров телефонов ==")
print(search_phone_numbers(transactions))

print("== Переводы частным лицам ==")
print(search_private_transfers(transactions))
