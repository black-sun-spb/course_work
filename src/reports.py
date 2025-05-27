# src/reports.py

import json
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

from src.decorators import save_result_to_file

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


@save_result_to_file("results.json")
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

        result_json = result_df.to_json(orient="records", force_ascii=False, indent=2, date_format="iso")

        logger.info(
            f"Отчет по категории '{category}' за период {start_date.date()} - {end_date.date()} успешно сформирован."
        )

        return result_json
    except Exception as e:
        logger.error(f"Ошибка при формировании отчета: {e}")
        return json.dumps({"error": str(e)})


@save_result_to_file("results.json")
def spending_by_weekday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    """
    Возвращает средние траты (отрицательные значения из "Сумма операции")
    по дням недели за последние 3 месяца от заданной даты (или текущей даты).

    :param transactions: DataFrame с колонками "Дата операции" и "Сумма операции"
    :param date: строка в формате 'YYYY-MM-DD' (по умолчанию — текущая дата)
    :return: DataFrame с колонками "День недели" и "Средняя сумма"
    """
    try:
        required_cols = {"Дата операции", "Сумма операции"}
        if not required_cols.issubset(transactions.columns):
            logging.warning(f"Отсутствуют нужные колонки: {required_cols - set(transactions.columns)}")
            return pd.DataFrame(columns=["День недели", "Средняя сумма"])

        df = transactions.copy()
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce", dayfirst=True)
        df["Сумма операции"] = pd.to_numeric(df["Сумма операции"], errors="coerce")

        df = df.dropna(subset=["Дата операции", "Сумма операции"])

        ref_date = pd.to_datetime(date) if date else pd.Timestamp.now()
        start_date = ref_date - pd.Timedelta(days=90)
        df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= ref_date)]

        df = df[df["Сумма операции"] < 0]

        if df.empty:
            return pd.DataFrame(columns=["День недели", "Средняя сумма"])

        day_mapping = {
            "Monday": "понедельник",
            "Tuesday": "вторник",
            "Wednesday": "среда",
            "Thursday": "четверг",
            "Friday": "пятница",
            "Saturday": "суббота",
            "Sunday": "воскресенье",
        }

        df["День недели"] = df["Дата операции"].dt.day_name().map(day_mapping)

        result = (
            df.groupby("День недели")["Сумма операции"]
            .mean()
            .abs()
            .round(2)
            .reset_index()
            .rename(columns={"Сумма операции": "Средняя сумма"})
        )

        return result

    except Exception as e:
        logging.exception(f"Ошибка в spending_by_weekday: {e}")
        return pd.DataFrame(columns=["День недели", "Средняя сумма"])


@save_result_to_file("results.json")
def spending_by_workday(transactions: pd.DataFrame, date: Optional[str] = None) -> pd.DataFrame:
    try:
        # Преобразование даты операции к типу datetime
        transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], dayfirst=True)

        # Определение референсной даты (переданная или текущая)
        ref_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()

        # Расчет даты начала периода (последние 3 месяца)
        start_date = ref_date - timedelta(days=90)

        # Фильтрация транзакций за последние 3 месяца с положительной суммой списания
        filtered = transactions[
            (transactions["Дата операции"] >= start_date)
            & (transactions["Дата операции"] <= ref_date)
            & (transactions["Сумма операции"] > 0)
        ].copy()

        # Определение типа дня (рабочий или выходной)
        filtered["Тип дня"] = filtered["Дата операции"].dt.weekday.map(
            lambda x: "Рабочий день" if x < 5 else "Выходной день"
        )

        # Расчет средних затрат по типу дня
        result = (
            filtered.groupby("Тип дня")["Сумма операции"]
            .mean()
            .round(2)
            .reset_index()
            .rename(columns={"Сумма операции": "Средние траты"})
        )

        return result

    except (KeyError, ValueError, TypeError) as error:
        logging.exception(f"Ошибка при формировании отчета по типу дня: {error}")
        return pd.DataFrame()
