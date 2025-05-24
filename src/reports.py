# src/reports.py

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from src.decorators import save_result_to_file

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


@save_result_to_file("expenses_report.json")
def expenses_by_category(df: pd.DataFrame, category: str, reference_date: datetime) -> str:
    """
    Возвращает расходы по категории за последние 3 месяца от даты reference_date.
    """
    try:
        required_columns = {"category", "date", "amount"}
        if not required_columns.issubset(df.columns):
            raise ValueError(f"DataFrame должен содержать колонки {required_columns}")

        df_category = df[df["category"] == category].copy()

        # Преобразование даты в datetime (чтобы избежать SettingWithCopyWarning)
        df_category["date"] = pd.to_datetime(df_category["date"])

        start_date = reference_date - timedelta(days=90)
        end_date = reference_date

        df_period = df_category[(df_category["date"] >= start_date) & (df_category["date"] <= end_date)]

        result_df = df_period.groupby(df_period["date"].dt.to_period("M")).agg({"amount": "sum"}).reset_index()
        result_df["date"] = result_df["date"].dt.to_timestamp()

        result_json = result_df.to_json(
            orient="records",
            force_ascii=False,
            indent=2,
            date_format="iso"
        )

        logger.info(
            f"Отчет по категории '{category}' за период {start_date.date()} - {end_date.date()} успешно сформирован."
        )

        return result_json
    except Exception as e:
        logger.error(f"Ошибка при формировании отчета: {e}")
        return json.dumps({"error": str(e)})


@save_result_to_file("results.json")
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> str:
    """
    Группирует транзакции по дням недели на русском языке,
    вычисляет среднюю сумму списания для каждого дня.
    Обрабатывает случаи отсутствия необходимых колонок.

    :param transactions: DataFrame с колонками "Дата операции" и "Сумма списания"
    :param date: строка в формате 'YYYY-MM-DD' для фильтрации по дате (опционально)
    :return: JSON строка с результатом
    """
    # Проверка наличия нужных колонок
    required_columns = ["Дата операции", "Сумма списания"]
    for col in required_columns:
        if col not in transactions.columns:
            # Возвращаем пустой DataFrame в виде JSON
            empty_df = pd.DataFrame(columns=["День недели", "Сумма списания"])
            return json.dumps(empty_df.to_dict(orient="records"), ensure_ascii=False)

    # Создаем копию данных для обработки
    filtered = transactions.copy()

    # Преобразуем дату в datetime
    filtered["Дата операции"] = pd.to_datetime(filtered["Дата операции"], errors="coerce")

    # Фильтрация по дате, если указана
    if date:
        date_obj = pd.to_datetime(date)
        filtered = filtered[filtered["Дата операции"] == date_obj]

    # Исключаем транзакции с нулевой или отрицательной суммой
    filtered = filtered[filtered["Сумма списания"] > 0]

    # Карта дней недели на русском
    day_mapping = {
        "Monday": "понедельник",
        "Tuesday": "вторник",
        "Wednesday": "среда",
        "Thursday": "четверг",
        "Friday": "пятница",
        "Saturday": "суббота",
        "Sunday": "воскресенье",
    }

    if not filtered.empty:
        filtered["День недели"] = filtered["Дата операции"].dt.day_name().map(day_mapping)
        result = filtered.groupby("День недели")["Сумма списания"].mean().reset_index()
    else:
        result = pd.DataFrame(columns=["День недели", "Сумма списания"])

    return json.dumps(result.to_dict(orient="records"), ensure_ascii=False)


def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    try:
        # Преобразование даты операции к типу datetime
        transactions["Дата операция"] = pd.to_datetime(transactions["Дата операция"], dayfirst=True)

        # Определение референсной даты (переданная или текущая)
        ref_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()

        # Расчет даты начала периода (последние 3 месяца)
        start_date = ref_date - timedelta(days=90)

        # Фильтрация транзакций за последние 3 месяца с положительной суммой списания
        filtered = transactions[
            (transactions["Дата операция"] >= start_date)
            & (transactions["Дата операция"] <= ref_date)
            & (transactions["Сумма списания"] > 0)
        ].copy()

        # Определение типа дня (рабочий или выходной)
        filtered["Тип дня"] = filtered["Дата операция"].dt.weekday.map(
            lambda x: "Рабочий день" if x < 5 else "Выходной день"
        )

        # Расчет средних затрат по типу дня
        result = (
            filtered.groupby("Тип дня")["Сумма списания"]
            .mean()
            .round(2)
            .reset_index()
            .rename(columns={"Сумма списания": "Средние траты"})
        )

        return result

    except (KeyError, ValueError, TypeError) as error:
        logging.exception(f"Ошибка при формировании отчета по типу дня: {error}")
        return pd.DataFrame()
