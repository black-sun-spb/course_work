# src/views.py

import pandas as pd
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
import os

from src.utils import get_greeting, parse_date, get_month_range, get_period_start

from src.options import (
    load_transactions,
    analyze_cards,
    get_top_transactions,
    fetch_currency_rates,
    fetch_stock_prices
)

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
        with open(str(SETTINGS_FILE), encoding='utf-8') as f:
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
            "stock_prices": stock_prices
        }

    except Exception as e:
        logging.exception("Ошибка при генерации данных главной страницы")
        return {"error": str(e)}


def generate_events_page_data(date_str: str, period: str = "M") -> dict:
    """Формирует JSON-ответ для страницы 'События' по заданной дате и периоду."""
    try:
        # Парсинг даты
        input_date = parse_date(date_str)
        start_date = get_period_start(input_date, period)
        end_date = input_date

        # Загрузка настроек
        with open(str(SETTINGS_FILE), encoding='utf-8') as f:
            settings = json.load(f)
        user_currencies = settings.get("user_currencies", [])
        user_stocks = settings.get("user_stocks", [])

        # Загрузка и фильтрация транзакций
        df = load_transactions(str(DATA_FILE))
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
        df = df[(df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)]

        # Расходы
        expenses_df = df[df["Сумма списания"] > 0]
        total_expenses = int(expenses_df["Сумма списания"].sum())

        # Основные траты
        main_exp = (
            expenses_df.groupby("Категория")["Сумма списания"]
            .sum()
            .sort_values(ascending=False)
        )
        main_exp = main_exp.drop(["Переводы", "Наличные"], errors="ignore")
        top7 = main_exp[:6].round().astype(int).reset_index()
        other_sum = main_exp[6:].sum()
        if other_sum > 0:
            top7 = top7.append({"Категория": "Остальное", "Сумма списания": int(other_sum)}, ignore_index=True)

        # Переводы и наличные
        transfers_cash = (
            expenses_df[expenses_df["Категория"].isin(["Переводы", "Наличные"])]
            .groupby("Категория")["Сумма списания"]
            .sum()
            .sort_values(ascending=False)
            .round()
            .astype(int)
            .reset_index()
        )

        # Поступления
        income_df = df[df["Сумма зачисления"] > 0]
        total_income = int(income_df["Сумма зачисления"].sum())
        main_income = (
            income_df.groupby("Категория")["Сумма зачисления"]
            .sum()
            .sort_values(ascending=False)
            .round()
            .astype(int)
            .reset_index()
        )

        # Валюты и акции
        currency_rates = fetch_currency_rates(user_currencies)
        stock_prices = fetch_stock_prices(user_stocks)

        return {
            "expenses": {
                "total_amount": total_expenses,
                "main": [
                    {"category": row["Категория"], "amount": row["Сумма списания"]}
                    for _, row in top7.iterrows()
                ],
                "transfers_and_cash": [
                    {"category": row["Категория"], "amount": row["Сумма списания"]}
                    for _, row in transfers_cash.iterrows()
                ]
            },
            "income": {
                "total_amount": total_income,
                "main": [
                    {"category": row["Категория"], "amount": row["Сумма зачисления"]}
                    for _, row in main_income.iterrows()
                ]
            },
            "currency_rates": currency_rates,
            "stock_prices": stock_prices
        }

    except Exception as e:
        logging.exception("Ошибка при генерации данных страницы 'События'")
        return {"error": str(e)}
