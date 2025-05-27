# tests/test_options.py

from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd

from src import options


# Тесты для analyze_cards
def test_analyze_cards_normal() -> None:
    data = {"Дата операции": ["2023-01-01", "2023-01-02"], "Номер карты": ["1234", "1234"], "Сумма операции": [100.5, 200.4]}
    df = pd.DataFrame(data)
    result = options.analyze_cards(df)
    assert result == {"1234": 301}


def test_analyze_cards_with_error() -> None:
    # Передача некорректных данных вызывает исключение
    df = pd.DataFrame({"Некорректные данные": [1, 2]})
    result = options.analyze_cards(df)
    assert result == {}


# Тесты для get_top_transactions
def test_get_top_transactions_normal() -> None:
    data = {"Дата операции": ["2023-01-01", "2023-01-02"], "Описание": ["desc1", "desc2"], "Сумма операции": [50, 150]}
    df = pd.DataFrame(data)
    top = options.get_top_transactions(df, top_n=1)
    assert len(top) == 1
    assert top[0]["Описание"] == "desc2"


def test_get_top_transactions_empty() -> None:
    df = pd.DataFrame({"Сумма операции": []})
    result = options.get_top_transactions(df)
    assert result == []


# Тесты для load_transactions
def test_load_transactions_valid(tmp_path: Path) -> None:
    # Создаем временный Excel файл без индекса
    df = pd.DataFrame({"A": [1, 2]})
    file_path = tmp_path / "test.xlsx"
    df.to_excel(file_path, index=False)  # добавьте index=False

    loaded_df = options.load_transactions(str(file_path))
    pd.testing.assert_frame_equal(df, loaded_df)


def test_load_transactions_invalid() -> None:
    result = options.load_transactions("nonexistent.xlsx")
    assert isinstance(result, pd.DataFrame)
    assert result.empty


# Тесты для fetch_stock_prices
@patch("requests.get")
def test_fetch_stock_prices_success(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "Global Quote": {
            "01. symbol": "AAPL",
            "05. price": "123.45"
        }
    }

    mock_get.return_value = mock_response

    stocks = ["AAPL"]

    with patch("os.getenv", return_value="fake_api_key"):
        result = options.fetch_stock_prices(stocks)

    assert result == [{"stock": "AAPL", "price": 123.45}]


@patch("requests.get")
def test_fetch_stock_prices_exception(mock_get: MagicMock) -> None:
    mock_get.side_effect = Exception("error")

    stocks = ["AAPL"]

    with patch("os.getenv", return_value="fake_api_key"):
        result = options.fetch_stock_prices(stocks)

    assert result == []


# Тесты для fetch_currency_rates
@patch("requests.get")
def test_fetch_currency_rates_success(mock_get: MagicMock) -> None:
    # Мокаем ответ API
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "rates": {"USD": 75.0, "EUR": 90.0}
    }
    mock_get.return_value = mock_response

    with patch("os.getenv", return_value="fake_api_key"):
        result = options.fetch_currency_rates(["USD", "EUR"])

    # Проверка результата
    assert isinstance(result, list)
    assert {"currency": "USD", "rate": 75.0} in result
    assert {"currency": "EUR", "rate": 90.0} in result


@patch("requests.get")
def test_fetch_currency_rates_api_error(mock_get: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    with patch("os.getenv", return_value="fake_api_key"):
        result = options.fetch_currency_rates(["USD"])
    assert result == []


@patch("requests.get")
def test_fetch_currency_rates_exception(mock_get: MagicMock) -> None:
    mock_get.side_effect = Exception("error")
    with patch("os.getenv", return_value="fake_api_key"):
        result = options.fetch_currency_rates(["USD"])
    assert result == []
