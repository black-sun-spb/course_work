import logging
import os
from typing import Any, Dict, List, Optional

import pandas as pd
import requests


def analyze_cards(df: pd.DataFrame) -> Dict[str, int]:
    try:
        required_cols = {"Дата операции", "Номер карты", "Сумма операции"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Отсутствуют нужные колонки: {required_cols - set(df.columns)}")

        df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")
        df["Сумма операции"] = pd.to_numeric(df["Сумма операции"], errors="coerce").fillna(0)
        filtered = df[df["Сумма операции"] > 0]

        return filtered.groupby("Номер карты")["Сумма операции"].sum().round().astype(int).to_dict()
    except Exception as e:
        logging.exception("Ошибка при анализе карт: %s", e)
        return {}


def get_top_transactions(df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
    try:
        required_cols = {"Дата операции", "Описание", "Сумма операции"}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Отсутствуют нужные колонки: {required_cols - set(df.columns)}")

        df["Сумма операции"] = pd.to_numeric(df["Сумма операции"], errors="coerce").fillna(0)
        df = df[df["Сумма операции"] > 0]
        top_df = df.sort_values("Сумма операции", ascending=False).head(top_n)

        records = top_df[["Дата операции", "Описание", "Сумма операции"]].to_dict(orient="records")
        return [{str(k): v for k, v in row.items()} for row in records]
    except Exception as e:
        logging.exception("Ошибка при получении топ-транзакций: %s", e)
        return []


def load_transactions(filepath: Optional[str] = None) -> pd.DataFrame:
    if filepath is None:
        filepath = os.path.join("data", "operations.xlsx")
    try:
        return pd.read_excel(filepath, index_col=None)
    except Exception as exc:
        logging.exception("Ошибка при загрузке транзакций из файла: %s", exc)
        return pd.DataFrame()


def fetch_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    try:
        api_key = os.getenv("ALPHAVANTAGE_API_KEY")
        base_url = "https://www.alphavantage.co/query"
        result = []

        for symbol in stocks:
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": api_key
            }
            response = requests.get(base_url, params=params)
            if response.status_code != 200:
                logging.warning("API error for %s: %s", symbol, response.status_code)
                continue

            data = response.json()

            # Проверка наличия данных
            global_quote = data.get("Global Quote")
            if not global_quote:
                logging.warning("Нет данных для акции %s", symbol)
                result.append({"stock": symbol, "price": 0})
                continue

            price_str = global_quote.get("05. price")
            if not price_str:
                logging.warning("Не получена цена для акции %s", symbol)
                result.append({"stock": symbol, "price": 0})
                continue

            try:
                price = round(float(price_str), 2)
            except ValueError:
                logging.warning("Некорректное значение цены для акции %s: %s", symbol, price_str)
                price = 0

            result.append({"stock": symbol, "price": price})

        return result
    except Exception as exc:
        logging.exception("Ошибка при получении цен акций: %s", exc)
        return []


def fetch_currency_rates(currencies: List[str]) -> List[Dict[str, float]]:
    """
    Получает курсы указанных валют по отношению к рублю (RUB)
    через API exchangerate.host (без фактической авторизации).

    :param currencies: Список валют (например, ["USD", "EUR"])
    :return: Список словарей вида {"currency": "USD", "rate": 0.013}
    """
    try:
        api_key = os.getenv("ALPHAVANTAGE_API_KEY", "dummy")

        url = "https://www.alphavantage.co/query"
        params = {
            "base": "RUB",
            "symbols": ",".join(currencies),
            "api_key": api_key  # Этот параметр игнорируется API, но включен для совместимости
        }

        response = requests.get(url, params=params)
        if response.status_code != 200:
            logging.warning("Ошибка при получении валют: %s - %s", response.status_code, response.text)
            return []

        rates = response.json().get("rates", {})
        return [{"currency": cur, "rate": round(rates.get(cur, 0), 2)} for cur in currencies]

    except Exception as exc:
        logging.exception("Ошибка при получении курсов валют:")
        return []