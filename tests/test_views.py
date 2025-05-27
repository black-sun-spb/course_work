# tests/test_views.py

import json
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd

from src.views import generate_events_page_data, generate_main_page_data


@patch("src.views.fetch_currency_rates")
@patch("src.views.fetch_stock_prices")
@patch("src.views.analyze_cards")
@patch("src.views.get_top_transactions")
@patch("src.views.load_transactions")
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps({"user_currencies": ["USD"], "user_stocks": ["AAPL"]}),
)
def test_generate_main_page_data(
    _: MagicMock,
    mock_load: MagicMock,
    mock_top: MagicMock,
    mock_cards: MagicMock,
    mock_stocks: MagicMock,
    mock_currency: MagicMock,
) -> None:
    # Создаем DataFrame с правильными колонками
    df = pd.DataFrame(
        {
            "Дата операции": ["01.05.2025", "15.05.2025"],
            "Сумма операции": [100, 200],
            "Категория": ["Еда", "Зарплата"],
        }
    )
    # Парсим даты
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)

    mock_load.return_value = df
    mock_top.return_value = [{"category": "Еда", "amount": 100}]
    mock_cards.return_value = {"Tinkoff": 300}
    mock_stocks.return_value = {"AAPL": 180.0}
    mock_currency.return_value = {"USD": 90.0}

    result = generate_main_page_data("2025-05-15 12:00:00")

    assert "greeting" in result
    assert result["cards"] == {"Tinkoff": 300}
    assert result["top_transactions"][0]["category"] == "Еда"
    assert result["currency_rates"]["USD"] == 90.0
    assert result["stock_prices"]["AAPL"] == 180.0


@patch("src.views.fetch_currency_rates")
@patch("src.views.fetch_stock_prices")
@patch("src.views.load_transactions")
@patch(
    "builtins.open",
    new_callable=mock_open,
    read_data=json.dumps({"user_currencies": ["USD"], "user_stocks": ["AAPL"]}),
)
def test_generate_events_page_data_success(
    _: MagicMock,
    mock_load_transactions: MagicMock,
    mock_fetch_stock_prices: MagicMock,
    mock_fetch_currency_rates: MagicMock,
) -> None:
    df = pd.DataFrame(
        {
            "Дата операции": ["2025-05-02", "2025-05-05", "2025-05-10", "2025-05-15"],
            "Сумма операции": [-100, -200, -50, 500],
            "Категория": ["Еда", "Переводы", "Еда", "Зарплата"],
        }
    )
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    mock_load_transactions.return_value = df
    mock_fetch_stock_prices.return_value = [{"stock": "AAPL", "price": 180.0}]
    mock_fetch_currency_rates.return_value = [{"currency": "USD", "rate": 90.0}]

    result = generate_events_page_data("2025-05-15 12:00:00", period="M")

    assert "expenses" in result
    assert "income" in result
    assert result["expenses"]["total_amount"] == -350  # -100 -200 -50 → abs sum
    assert result["income"]["total_amount"] == 500
