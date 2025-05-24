# src/views.py

import json
import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from src.options import (
    analyze_cards,
    fetch_currency_rates,
    fetch_stock_prices,
    get_top_transactions,
    load_transactions,
)
from src.utils import get_greeting, get_month_range, get_period_start, parse_date

# Пути к данным
DATA_FILE = Path(os.getenv("DATA_FILE", "data/operations.xlsx"))
SETTINGS_FILE = Path(os.getenv("SETTINGS_FILE", "user_settings.json"))

load_dotenv()

API_KEY = os.getenv("FINNHUB_API_KEY")


def generate_main_page_data(date_str: str) -> dict:
    """Главная функция: принимает дату, возвращает JSON-ответ для страницы."""
    try:
        # Парсинг входящей даты и расчет диапазона
        input_date = parse_date(date_str)
        start_date, end_date = get_month_range(input_date)

        # Загрузка пользовательских настроек
        with open(str(SETTINGS_FILE), encoding="utf-8") as f:
            settings = json.load(f)

        user_currencies = settings.get("user_currencies", [])
        user_stocks = settings.get("user_stocks", [])

        # Загрузка и фильтрация транзакций
        df = load_transactions(str(DATA_FILE))
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
        df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]

        # Приветствие
        greeting = get_greeting(input_date)

        # Анализ по картам
        cards_summary = analyze_cards(df)

        # Топ-5 транзакций
        top_txns = get_top_transactions(df, top_n=5)

        # Внешние данные
        currency_rates = fetch_currency_rates(user_currencies)
        stock_prices = fetch_stock_prices(user_stocks)

        return {
            "greeting": greeting,
            "cards": cards_summary,
            "top_transactions": top_txns,
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }

    except Exception as e:
        logging.exception("Ошибка при генерации данных главной страницы")
        return {"error": str(e)}


def generate_events_page_data(date_str: str, period: str = "M") -> dict:
    """Формирует JSON-ответ для страницы 'События' по заданной дате и периоду."""
    e = None
    result_data = None

    try:
        input_date = parse_date(date_str)
        start_date = get_period_start(input_date, period)
        end_date = input_date

        with open(str(SETTINGS_FILE), encoding="utf-8") as f:
            settings = json.load(f)
        user_currencies = settings.get("user_currencies", [])
        user_stocks = settings.get("user_stocks", [])

        df = load_transactions(str(DATA_FILE))

        required_cols = ["Дата операция", "Сумма списания", "Сумма зачисления", "Категория"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Отсутствует колонка: {col}")

        df["Дата операция"] = pd.to_datetime(df["Дата операция"], errors="coerce", dayfirst=True)
        df.dropna(subset=["Дата операция"], inplace=True)

        df["Сумма списания"] = pd.to_numeric(df["Сумма списания"], errors="coerce").fillna(0)
        df["Сумма зачисления"] = pd.to_numeric(df["Сумма зачисления"], errors="coerce").fillna(0)

        df_period = df[(df["Дата операция"] >= start_date) & (df["Дата операция"] <= end_date)]

        if df_period.empty:
            logging.warning("Нет транзакций за выбранный период")

        expenses_df = df_period[df_period["Сумма списания"] > 0]
        logging.info(f"Expenses DataFrame:\n{expenses_df}")
        total_expenses = int(expenses_df["Сумма списания"].sum())

        main_exp = (
            expenses_df.groupby("Категория")["Сумма списания"]
            .sum()
            .sort_values(ascending=False)
            .drop(["Переводы", "Наличные"], errors="ignore")
        )

        top7 = main_exp[:6].round().astype(int).reset_index()

        other_sum = main_exp[6:].sum()
        if other_sum > 0:
            other_df = pd.DataFrame([{"Категория": "Остальное", "Сумма списания": int(other_sum)}])
            top7 = pd.concat([top7, other_df], ignore_index=True)

        transfers_cash = (
            expenses_df[expenses_df["Категория"].isin(["Переводы", "Наличные"])]
            .groupby("Категория")["Сумма списания"]
            .sum()
            .sort_values(ascending=False)
            .round()
            .astype(int)
            .reset_index()
        )

        income_df = df_period[df_period["Сумма зачисления"] > 0]
        total_income = int(income_df["Сумма зачисления"].sum())

        main_income = (
            income_df.groupby("Категория")["Сумма зачисления"]
            .sum()
            .sort_values(ascending=False)
            .round()
            .astype(int)
            .reset_index()
        )

        currency_rates = fetch_currency_rates(user_currencies)
        stock_prices = fetch_stock_prices(user_stocks)

        result_data = {
            "expenses": {
                "total_amount": total_expenses,
                "main": [
                    {"category": row["Категория"], "amount": row["Сумма списания"]} for _, row in top7.iterrows()
                ],
                "transfers_and_cash": [
                    {"category": row["Категория"], "amount": row["Сумма списания"]}
                    for _, row in transfers_cash.iterrows()
                ],
            },
            "income": {
                "total_amount": total_income,
                "main": [
                    {"category": row["Категория"], "amount": row["Сумма зачисления"]}
                    for _, row in main_income.iterrows()
                ],
            },
            "currency_rates": currency_rates,
            "stock_prices": stock_prices,
        }

    except Exception as exc:
        e = exc
        logging.exception("Ошибка при генерации данных страницы 'События'")
    finally:
        return result_data if result_data is not None else {"error": str(e) if e else "Произошла неизвестная ошибка"}
