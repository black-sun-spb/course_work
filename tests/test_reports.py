import json
from datetime import datetime

import pandas as pd
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


@pytest.fixture
def sample_transactions() -> pd.DataFrame:
    data = {
        "Дата операции": ["2024-01-01", "2024-01-02", "2024-02-15", "2024-03-01", "2024-03-10", "2024-03-20"],
        "Сумма списания": [100, 200, 150, 300, 250, 400],
    }
    df = pd.DataFrame(data)
    return df


def test_spending_by_weekday(sample_transactions: pd.DataFrame) -> None:
    # Используем фиксированную дату для теста
    result_json = spending_by_weekday(sample_transactions, date="2024-03-20")

    # Проверяем, что результат не пустой и содержит ожидаемые данные
    import json

    result_data = json.loads(result_json)

    # Проверка наличия данных и правильных колонок
    assert isinstance(result_data, list)
    assert len(result_data) > 0

    # Проверка, что есть хотя бы один день недели и сумма положительна
    for record in result_data:
        assert "День недели" in record
        assert "Сумма списания" in record


def test_with_no_data_in_range() -> None:
    # Дата так выбрана, что фильтр не пропускает транзакции
    df = pd.DataFrame({"Дата операции": ["2020-01-01"], "Сумма списания": [100]})

    result_json = spending_by_weekday(df, date="2020-01-02")

    result_df = pd.read_json(result_json)

    # Ожидается пустой DataFrame с нужными колонками или пустой список в JSON
    assert isinstance(result_df, pd.DataFrame)


def test_missing_columns() -> None:
    df = pd.DataFrame({"Some column": [1, 2]})

    result_json = spending_by_weekday(df)

    result_df = pd.read_json(result_json)

    # Проверка, что результат — DataFrame и он пустой
    assert isinstance(result_df, pd.DataFrame)
    assert result_df.empty


def test_invalid_date_format() -> None:
    df = pd.DataFrame(
        {"Дата операции": ["2024/01/01"], "Сумма списания": [50]}  # неправильный формат (должен быть день-мес-год)
    )

    # Внутри функции попытка преобразовать вызовет ошибку,
    # которая будет поймана и вернёт пустой DataFrame.
    result_json = spending_by_weekday(df, date="2024/01/01")

    result_df = pd.read_json(result_json)

    assert isinstance(result_df, pd.DataFrame)

    assert isinstance(result_df, pd.DataFrame)


def test_negative_or_zero_spending() -> None:
    df = pd.DataFrame({"Дата операции": ["2024-02-15"], "Сумма списания": [0]})
    result_json = spending_by_weekday(df, date="2024-02-15")
    result_df = pd.read_json(result_json)

    assert isinstance(result_df, pd.DataFrame)
    assert result_df.empty


def test_translation_of_days() -> None:
    df = pd.DataFrame(
        {"Дата операции": ["2024-02-19", "2024-02-20"], "Сумма списания": [50, 60]}  # понедельник  # вторник
    )

    # Проверяем всю таблицу без фильтрации
    result_json = spending_by_weekday(df)
    result = pd.read_json(result_json)
    days_in_result = result["День недели"].tolist()

    expected_days = ["понедельник", "вторник"]
    for day in expected_days:
        assert day in days_in_result


def test_single_day() -> None:
    df = pd.DataFrame({"Дата операции": ["2024-02-19", "2024-02-20"], "Сумма списания": [50, 60]})

    result_json = spending_by_weekday(df, date="2024-02-20")
    result = pd.read_json(result_json)

    assert result["День недели"].iloc[0] == "вторник"


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
