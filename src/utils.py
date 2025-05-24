# src/utils.py

import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional


def parse_date(date_str: str) -> datetime:
    """
    Преобразует строку с датой формата 'YYYY-MM-DD HH:MM:SS' в объект datetime.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError as parse_error:
        logging.error("Неверный формат даты: %s", date_str)
        raise parse_error


def get_month_range(input_date: datetime) -> Tuple[datetime, datetime]:
    """
    Возвращает первое и последнее число месяца для заданной даты.
    """
    start = input_date.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end = start.replace(month=start.month + 1, day=1) - timedelta(days=1)
    return start, end


def get_period_start(end_date: datetime, period: str) -> datetime:
    """
    Вычисляет дату начала периода на основе выбранного диапазона: W, M, Y, ALL.
    """
    if period == "W":
        return end_date - timedelta(days=6)
    elif period == "M":
        return end_date.replace(day=1)
    elif period == "Y":
        return end_date.replace(month=1, day=1)
    elif period == "ALL":
        return datetime(2000, 1, 1)
    else:
        logging.warning("Неизвестный период '%s', используется месяц", period)
        return end_date.replace(day=1)


def get_greeting(current_time: Optional[datetime] = None) -> str:
    """
    Возвращает приветствие в зависимости от времени суток.

    :param current_time: необязательное время (по умолчанию текущее)
    :return: строка с приветствием
    """
    now = current_time or datetime.now()
    hour = now.hour

    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"