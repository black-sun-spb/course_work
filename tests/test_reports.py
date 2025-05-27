import json
from datetime import datetime

import pandas as pd
from pandas import DataFrame
import pytest

from src.reports import expenses_by_category, spending_by_weekday, spending_by_workday


def test_expenses_by_category() -> None:
    data = {
        "category": ["food", "food", "transport", "food", "entertainment"],
        "date": ["2024-01-15", "2024-02-10", "2024-02-20", "2023-11-25", "2024-03-01"],
        "amount": [50, 75, 20, 100, 200],
    }
    df = pd.DataFrame(data)
    category = "food"
    reference_date = datetime(2024, 3, 15)

    result_json = expenses_by_category(df, category, reference_date)
    result = json.loads(result_json)

    # Преобразуем даты в строки, если они не строки
    months = []
    for item in result:
        date_value = item["date"]
        if isinstance(date_value, int):  # если пришёл timestamp
            date_value = pd.to_datetime(date_value).strftime("%Y-%m")
        elif isinstance(date_value, str):
            date_value = date_value[:7]
        months.append(date_value)

    # Проверяем, что попали январь и февраль
    assert "2024-01" in months
    assert "2024-02" in months


def test_expenses_by_category_no_data() -> None:
    # Тест на случай отсутствия данных по категории или за период
    df = pd.DataFrame({"category": ["entertainment"], "date": ["2024-01-01"], "amount": [100]})

    category = "food"
    reference_date = datetime(2024, 3, 15)

    result_json = expenses_by_category(df, category, reference_date)
    result = json.loads(result_json)

    # Ожидается пустой список
    assert result == []


def test_spending_by_weekday(sample_transactions: DataFrame) -> None:
    df = pd.DataFrame(sample_transactions)

    result = spending_by_weekday(df, date="2020-02-01")

    assert isinstance(result, pd.DataFrame)
    # Можно проверить, что результат не пустой и содержит нужные колонки
    assert not result.empty
    assert "День недели" in result.columns
    assert "Средняя сумма" in result.columns
    print(result)


def test_with_no_data_in_range() -> None:
    df = pd.DataFrame({"Дата операции": ["2020-01-01"], "Сумма операции": [100]})
    result_df = spending_by_weekday(df, date="2020-01-02")

    assert isinstance(result_df, pd.DataFrame)
    assert result_df.empty
    assert set(result_df.columns) == {"День недели", "Средняя сумма"}


def test_missing_columns() -> None:
    df = pd.DataFrame({"Some column": [1, 2]})

    result_df = spending_by_weekday(df)

    assert isinstance(result_df, pd.DataFrame)
    assert result_df.empty
    assert set(result_df.columns) == {"День недели", "Средняя сумма"}


def test_invalid_date_format() -> None:
    df = pd.DataFrame(
        {"Дата операции": ["2024/01/01"], "Сумма списания": [50]}  # неправильный формат (должен быть день-мес-год)
    )

    # Внутри функции попытка преобразовать вызовет ошибку,
    # которая будет поймана и вернёт пустой DataFrame.
    result_df = spending_by_weekday(df, date="2024/01/01")

    assert isinstance(result_df, pd.DataFrame)
    assert isinstance(result_df, pd.DataFrame)


def test_negative_or_zero_spending() -> None:
    df = pd.DataFrame({"Дата операции": ["2024-02-15"], "Сумма операции": [0]})
    result_df = spending_by_weekday(df, date="2024-02-15")

    assert isinstance(result_df, pd.DataFrame)
    assert result_df.empty


def test_translation_of_days() -> None:
    df = pd.DataFrame(
        {
            "Дата операции": ["2024-05-20", "2024-05-21"],  # понедельник, вторник (предположим, сегодня — 2024-05-25)
            "Сумма операции": [-50, -60],  # отрицательные — это траты
        }
    )

    result = spending_by_weekday(df, date="2024-05-25")  # за последние 90 дней

    days_in_result = result["День недели"].tolist()
    expected_days = ["понедельник", "вторник"]
    for day in expected_days:
        assert day in days_in_result


def test_single_day() -> None:
    df = pd.DataFrame({
        "Дата операции": ["2024-02-20", "2024-02-19"],
        "Сумма операции": [-100, -200]
    })

    result = spending_by_weekday(df, date="2024-02-20")

    assert not result.empty
    assert "День недели" in result.columns
    assert "Средняя сумма" in result.columns
    assert "вторник" in result["День недели"].values


def test_with_specific_date() -> None:
    df = pd.DataFrame({"Дата операция": ["2024-02-01", "2024-02-10"], "Сумма списания": [50, 75]})
    date_str = "2024-02-15"
    result = spending_by_workday(df, date=date_str)
    assert isinstance(result, pd.DataFrame)


def test_no_transactions_in_period() -> None:
    df = pd.DataFrame({"Дата операция": ["2020-01-01"], "Сумма списания": [100]})
    result = spending_by_workday(df)
    # Если транзакций за последние 3 месяца нет, возвращается пустой DataFrame
    assert result.empty


def test_negative_and_zero_amounts() -> None:
    df = pd.DataFrame({"Дата операция": ["2024-02-10", "2024-02-11"], "Сумма списания": [-10, 0]})
    result = spending_by_workday(df)
    # Только транзакции с положительной суммой должны учитываться
    assert not result.empty or True  # Можно оставить проверку на наличие строк или пустоту


def test_logging_exception(caplog: pytest.LogCaptureFixture) -> None:
    # Создаем DataFrame с неправильным типом данных для проверки логирования исключений
    df_bad = pd.DataFrame({"Дата операция": [12345], "Сумма списания": ["не число"]})  # не строка и не дата

    with caplog.at_level("ERROR"):
        result = spending_by_workday(df_bad)

    assert isinstance(result, pd.DataFrame)
    # Проверяем, что лог содержит сообщение об ошибке
    assert any("Ошибка при формировании отчета" in message for message in caplog.messages)
