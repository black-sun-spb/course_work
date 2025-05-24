import requests
import pandas as pd
from typing import List, Dict, Any
import os
import logging

def analyze_cards(df: pd.DataFrame) -> Dict[str, int]:
    """
    Анализирует транзакции по картам, суммируя списания по каждой карте.

    Параметры:
        df (pd.DataFrame): DataFrame с транзакциями, должен содержать колонки "Дата операции", "Карта" и "Сумма списания".

    Возвращает:
        Dict[str, int]: словарь, где ключ — номер карты, значение — сумма списаний (округленная до целого).
        В случае ошибки возвращает пустой словарь.
    """
    try:
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%Y-%m-%d")
        filtered = df[df["Сумма списания"] > 0]
        return filtered.groupby("Карта")["Сумма списания"].sum().round().astype(int).to_dict()
    except Exception as e:
        logging.exception("Ошибка при анализе карт: %s", e)
        return {}

def get_top_transactions(df: pd.DataFrame, top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Получает топ-N транзакций по сумме списаний.

    Параметры:
        df (pd.DataFrame): DataFrame с транзакциями, должен содержать колонки "Дата операции", "Описание" и "Сумма списания".
        top_n (int): количество топ-транзакций для возврата.

    Возвращает:
        List[Dict[str, Any]]: список словарей с информацией о транзакциях ("Дата операции", "Описание", "Сумма списания").
        В случае ошибки возвращает пустой список.
    """
    try:
        top_df = df[df["Сумма списания"] > 0].sort_values("Сумма списания", ascending=False).head(top_n)
        return top_df[["Дата операции", "Описание", "Сумма списания"]].to_dict(orient="records")
    except Exception as e:
        logging.exception("Ошибка при получении топ-транзакций: %s", e)
        return []

def load_transactions(filepath: str = None) -> pd.DataFrame:
    """
    Загружает транзакции из Excel-файла.
    Если путь не указан, по умолчанию использует 'data/operations.xlsx'.

    Параметры:
        filepath (str): путь к файлу Excel. По умолчанию 'data/operations.xlsx'.

    Возвращает:
        pd.DataFrame: DataFrame с данными транзакций.
        В случае ошибки возвращает пустой DataFrame.
    """
    if filepath is None:
        filepath = os.path.join("data", "operations.xlsx")
    try:
        return pd.read_excel(filepath, index_col=None)
    except Exception as exc:
        logging.exception("Ошибка при загрузке транзакций из файла: %s", exc)
        return pd.DataFrame()

def fetch_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    """
    Получает текущие цены акций по списку символов через API Finnhub.

    Параметры:
        stocks (List[str]): список символов акций.

    Возвращает:
        List[Dict[str, Any]]: список словарей с ключами "stock" и "price".
                              Если произошла ошибка или цена не получена — цена равна 0.
                              В случае исключения возвращается пустой список.
    """
    try:
        api_key = os.getenv("FINNHUB_API_KEY")
        base_url = "https://finnhub.io/api/v1/quote"
        result = []

        for symbol in stocks:
            params = {"symbol": symbol, "token": api_key}
            response = requests.get(base_url, params=params)
            if response.status_code != 200:
                logging.warning("API error for %s: %s", symbol, response.status_code)
                continue

            data = response.json()
            price = round(data.get("c", 0), 2)
            if price == 0:
                logging.warning("Не получена цена для акции %s", symbol)
            result.append({"stock": symbol, "price": price})

        return result
    except Exception as exc:
        logging.exception("Ошибка при получении цен акций: %s", exc)
        return []

def fetch_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    """
    Получает текущие курсы валют относительно рубля через API Finnhub.

    Параметры:
        currencies (List[str]): список валютных кодов для получения курса.

    Возвращает:
        List[Dict[str, Any]]: список словарей с ключами "currency" и "rate".
                              Если произошла ошибка или курс не получен — значение равно 0.
                              В случае исключения возвращается пустой список.
    """
    try:
        api_key = os.getenv("FINNHUB_API_KEY")
        base_url = "https://finnhub.io/api/v1/forex/rates"
        params = {"base": "RUB", "token": api_key}
        response = requests.get(base_url, params=params)

        if response.status_code != 200:
            logging.warning("API error при получении валют: %s", response.status_code)
            return []

        data = response.json().get("quote", {})
        result = []

        for currency in currencies:
            rate = round(data.get(currency, 0), 2)
            result.append({"currency": currency, "rate": rate})

        return result
    except Exception as exc:
        logging.exception("Ошибка при получении курсов валют: %s", exc)
        return []