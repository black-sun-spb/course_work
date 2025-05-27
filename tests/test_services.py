import json
from typing import Any

from src.services import (analyze_cashback_categories, investment_bank, search_phone_numbers, search_private_transfers,
                          simple_search)


def test_analyze_cashback_categories_february(samp_transactions: list[dict[str, Any]]) -> None:
    result_json = analyze_cashback_categories(samp_transactions, 2024, 2)
    result = json.loads(result_json)

    expected = {
        "Еда": round((1000 + 200) * 0.05),  # (1200 * 0.05) = 60
        "Транспорт": round(500 * 0.05),  # (500 * 0.05) = 25
    }

    assert result == expected


def test_no_transactions_for_month(sample_transactions: list[dict[str, Any]]) -> None:
    result_json = analyze_cashback_categories(sample_transactions, 2023, 8)
    result = json.loads(result_json)
    assert result == {}


def test_no_transactions_in_month_with_fixture(simple_transactions: list[dict[str, Any]]) -> None:
    result_json = investment_bank("2023-08", simple_transactions, savings_goal=50)
    result = json.loads(result_json)
    # В августе транзакций нет
    assert result["сумма"] == 0


def test_invalid_date_format_with_fixture() -> None:
    transactions = [
        {"Дата операции": "2023/07/10", "Сумма операции": 100},
        {"Дата операции": "not-a-date", "Сумма операции": 50},
    ]
    result_json = investment_bank("2023-07", transactions, savings_goal=50)
    result = json.loads(result_json)
    # Все транзакции некорректны по дате, сумма должна быть нулевой
    assert result["сумма"] == 0


def test_large_amounts_with_fixture() -> None:
    transactions = [{"Дата операции": "2023-07-01", "Сумма операции": 1234.56}]
    result_json = investment_bank("2023-07", transactions, savings_goal=50)
    result = json.loads(result_json)
    print("Результат суммы:", result["сумма"])
    expected_difference = round(1250 - 1234.56, 2)
    print("Ожидаемое значение:", expected_difference)
    assert abs(result["сумма"] - expected_difference) < 1e-6


def test_simple_search_found() -> None:
    transactions = [
        {"Описание": "Покупка в магазине", "Сумма": 100},
        {"Описание": "Оплата коммунальных услуг", "Сумма": 50},
        {"Описание": "Покупка в магазине электроники", "Сумма": 200},
    ]
    keyword = "магазин"
    result_json = simple_search(transactions, keyword)
    result = json.loads(result_json)

    assert isinstance(result, list)
    assert len(result) == 2
    assert all("магазин" in txn["Описание"].lower() for txn in result)


def test_simple_search_not_found() -> None:
    transactions = [
        {"Описание": "Покупка в магазине", "Сумма": 100},
        {"Описание": "Оплата коммунальных услуг", "Сумма": 50},
    ]
    keyword = "авто"
    result_json = simple_search(transactions, keyword)
    result = json.loads(result_json)

    assert isinstance(result, list)
    assert len(result) == 0


def test_simple_search_empty_transactions() -> None:
    transactions: list[dict[str, Any]] = []
    keyword = "любое"
    result_json = simple_search(transactions, keyword)
    result = json.loads(result_json)

    assert result == []


def test_simple_search_missing_description() -> None:
    transactions: list[dict[str, Any]] = [{"Сумма": 100}, {"Описание": "Покупка", "Сумма": 50}]
    keyword = "покупка"
    result_json = simple_search(transactions, keyword)
    result = json.loads(result_json)

    # Должен найти только транзакцию с описанием
    assert len(result) == 1
    assert result[0]["Описание"] == "Покупка"


def test_simple_search_case_insensitivity() -> None:
    transactions = [{"Описание": "Купил книгу", "Сумма": 300}]
    keyword_upper = "КУПИЛ"
    keyword_lower = "купил"

    result_upper = json.loads(simple_search(transactions, keyword_upper))
    result_lower = json.loads(simple_search(transactions, keyword_lower))

    assert result_upper == result_lower


def test_search_phone_numbers_found() -> None:
    txns = [
        {"Описание": "Позвоните по номеру +7 123 456 78 90 для консультации", "Сумма": 100},
        {"Описание": "Нет номера", "Сумма": 50},
        {"Описание": "Контакт: +7-987-654-32-10", "Сумма": 200},
    ]
    result_json = search_phone_numbers(txns)
    result = json.loads(result_json)

    assert isinstance(result, list)
    # Проверьте сколько номеров было найдено
    assert len(result) == 2

    # Проверяем, что оба описания содержат номера
    descriptions = [txn["Описание"] for txn in result]
    assert any("+7" in desc for desc in descriptions)


def test_search_phone_numbers_not_found() -> None:
    txns = [{"Описание": "Нет номера телефона", "Сумма": 100}, {"Описание": "Общая информация", "Сумма": 50}]
    result_json = search_phone_numbers(txns)
    result = json.loads(result_json)

    assert isinstance(result, list)
    assert len(result) == 0


def test_search_phone_numbers_empty() -> None:
    txns: list[dict[str, Any]] = []
    result_json = search_phone_numbers(txns)
    result = json.loads(result_json)

    assert result == []


def test_search_phone_numbers_various_formats() -> None:
    txns = [
        {"Описание": "Позвоните +7 123 456 78 90", "Сумма": 100},
        {"Описание": "Номер: +7-321-654-98-76", "Сумма": 200},
        {"Описание": "Некорректный номер +71234567890", "Сумма": 300},  # без пробелов и дефисов
        {"Описание": "Неверный формат +8 999 999 99 99", "Сумма": 400},
    ]
    result_json = search_phone_numbers(txns)
    result = json.loads(result_json)

    # Должны найти только те номера, которые начинаются с +7 и соответствуют шаблону
    assert len(result) == 3

    # Проверяем, что все найденные номера начинаются с +7
    for entry in result:
        assert entry["Номер"].startswith("+7")

    # Проверяем наличие конкретных номеров
    found_numbers = [entry["Номер"] for entry in result]
    assert "+7 123 456 78 90" in found_numbers
    assert "+7-321-654-98-76" in found_numbers
    assert "+71234567890" in found_numbers


if __name__ == "__main__":
    test_search_phone_numbers_various_formats()


def test_search_phone_numbers_case_insensitivity() -> None:
    txns = [{"Описание": "Позвоните по номеру +7 123 456 78 90", "Сумма": 100}]

    # В шаблоне регистронезависимый поиск не нужен, так как номера начинаются с +7.
    # Но можно проверить, что поиск работает независимо от регистра текста.

    # В данном случае, шаблон ищет "+7" в тексте, регистр не важен.

    result_json_upper = search_phone_numbers(txns)
    result_upper = json.loads(result_json_upper)

    assert len(result_upper) == 1


def test_search_private_transfers_with_sample(sample_transactions: list[dict[str, Any]]) -> None:
    # Предположим, что функция ищет транзакции категории 'Переводы' с описанием,
    # содержащим шаблон (например, имя и инициалы).
    # В текущих данных нет таких транзакций, ожидаем результат - пустой список.
    result_json = search_private_transfers(sample_transactions)
    result = json.loads(result_json)
    assert isinstance(result, list)
    assert result == []


def test_search_private_transfers_with_mocked_data() -> None:
    # Создадим транзакции с нужным шаблоном в описании.
    transactions = [
        {"Категория": "Переводы", "Описание": "Иванов А. перевел деньги"},
        {"Категория": "Переводы", "Описание": "Петров П. перевел деньги"},
        {"Категория": "Переводы", "Описание": "Общая операция"},
    ]
    result_json = search_private_transfers(transactions)
    result = json.loads(result_json)
    # Проверяем, что вернулись только те транзакции, где описание содержит шаблон.
    assert len(result) == 2
    descriptions = [txn["Описание"] for txn in result]
    assert any("Иванов А." in desc for desc in descriptions)
    assert any("Петров П." in desc for desc in descriptions)


def test_search_private_transfers_no_matches() -> None:
    transactions = [{"Категория": "Еда", "Описание": ""}, {"Категория": "Транспорт", "Описание": ""}]
    result_json = search_private_transfers(transactions)
    result = json.loads(result_json)
    assert result == []


def test_search_private_transfers_with_negative_and_other_categories() -> None:
    transactions: list[dict[str, Any]] = [
        {"Категория": "Переводы", "Описание": None},
        {"Категория": None, "Описание": ""},
        {"Категория": "", "Описание": ""},
        {"Категория": "Переводы", "Описание": ""},
        {"Категория": "", "Описание": None},
    ]
    result_json = search_private_transfers(transactions)
    result = json.loads(result_json)
    assert result == []
