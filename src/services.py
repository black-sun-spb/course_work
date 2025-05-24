# src/services.py

import json
import logging
import math
import re
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def analyze_cashback_categories(
        transactions_list: List[Dict[str, Any]],
        year: int,
        month: int
) -> str:
    """
    Анализирует категории повышенного кешбэка за указанный месяц.

    :param transactions_list: список транзакций
    :param year: год для анализа
    :param month: месяц для анализа
    :return: JSON-строка с категориями и суммой кешбэка
    """
    df = pd.DataFrame(transactions_list)

    # Проверяем существующие названия для даты
    possible_date_keys = ["Дата операция", "Дата операции"]
    date_key = next((k for k in possible_date_keys if k in df.columns), None)

    required_columns = {"Категория", "Сумма списания"}
    if not date_key or not required_columns.issubset(df.columns):
        return json.dumps({})

    df[date_key] = pd.to_datetime(df[date_key], errors="coerce")
    df = df.dropna(subset=[date_key])

    # Фильтрация по году и месяцу
    df_filtered = df[
        (df[date_key].dt.year == year) & (df[date_key].dt.month == month)
        ]
    df_filtered = df_filtered[df_filtered["Сумма списания"] > 0]

    # Группировка по категориям
    grouped = df_filtered.groupby("Категория")["Сумма списания"].sum()

    cashback_rate = 0.05
    result: Dict[str, int] = {
        str(category): round(total * cashback_rate) for category, total in grouped.items()
    }

    return json.dumps(result)


def investment_bank(month: str, transactions: List[Dict], savings_goal: int = 50) -> str:
    """
    Расчёт суммы сэкономленных средств за указанный месяц в рамках инвесткопилки.

    :param month: Месяц в формате 'YYYY-MM'
    :param transactions: Список транзакций
    :param savings_goal: Лимит округления (по умолчанию 50)
    :return: JSON-строка с общей сэкономленной суммой
    """
    total_saved = 0

    filtered_transactions = []
    for t in transactions:
        date_str = t["Дата операции"]
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            if date_obj.strftime("%Y-%m") == month:
                filtered_transactions.append(t)
        except ValueError:
            logger.warning(f"Некорректный формат даты: {date_str}")

    if not filtered_transactions:
        return json.dumps({"сумма": 0})

    for transaction in filtered_transactions:
        amount = transaction["Сумма операции"]
        logger.info(f"Обрабатываем транзакцию: {amount}")
        rounded = ((math.ceil(amount) + savings_goal - 1) // savings_goal) * savings_goal
        logger.info(f"Округленная сумма: {rounded}")
        diff = round(rounded - amount, 2)
        logger.info(f"Разница: {diff}")
        total_saved += diff

    logger.info(f"Общий сэкономленный итог внутри функции: {total_saved}")
    return json.dumps({"сумма": total_saved})


def simple_search(transactions: List[Dict], keyword: str) -> str:
    """
    Выполняет поиск транзакций по ключевому слову в поле 'Описание' и возвращает результат в виде JSON-строки.

    :param transactions: список транзакций (словарей)
    :param keyword: строка для поиска
    :return: JSON-строка с найденными транзакциями
    """
    try:
        # Логируем входные параметры
        logging.info(f"Запуск простого поиска по ключевому слову: {keyword}")

        # Выполняем поиск
        result = [txn for txn in transactions if keyword.lower() in txn.get("Описание", "").lower()]

        # Логируем количество найденных транзакций
        logging.info(f"Найдено транзакций: {len(result)}")

        # Возвращаем результат в виде JSON-строки
        return json.dumps(result)
    except Exception as e:
        logging.exception(f"Ошибка при выполнении простого поиска: {e}")
        return json.dumps([])


def search_phone_numbers(txns: List[Dict[str, Any]]) -> str:
    """
    Ищет телефонные номера в транзакциях по шаблону и возвращает результат в виде JSON.
    """
    try:
        # Обновленный шаблон для поиска номеров +7 с пробелами или дефисами
        phone_pattern = re.compile(r"\+7(?:[\s\-])?\d{3}(?:[\s\-])?\d{3}(?:[\s\-])?\d{2}(?:[\s\-])?\d{2}")
        result = []

        for txn in txns:
            description = txn.get("Описание", "")
            # Используем finditer(), чтобы получить все совпадения
            for match in phone_pattern.finditer(description):
                number = match.group()
                result.append({"Номер": number, "Описание": description, "Сумма": txn.get("Сумма")})

        return json.dumps(result)
    except Exception:
        logging.exception("Ошибка при поиске телефонных номеров")
        return json.dumps([])


def search_private_transfers(transactions: List[Dict]) -> str:
    try:
        pattern = re.compile(r"\b[А-ЯЁ][а-яё]+ [А-ЯЁ]\.(?!\S)")

        def is_private_transfer(txn: Dict) -> bool:
            description = txn.get("Описание", "")
            return txn.get("Категория") == "Переводы" and bool(pattern.search(description))

        filtered_transactions = list(filter(is_private_transfer, transactions))
        return json.dumps(filtered_transactions)
    except Exception as e:
        logging.exception("Ошибка при поиске переводов физическим лицам: %s", e)
        return json.dumps([])
