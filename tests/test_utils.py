from datetime import datetime

import pytest

from src.utils import get_greeting, get_month_range, get_period_start, parse_date


def test_parse_date_valid() -> None:
    date_str = "2025-05-23 14:30:00"
    result = parse_date(date_str)
    assert result == datetime(2025, 5, 23, 14, 30, 0)


def test_parse_date_invalid() -> None:
    with pytest.raises(ValueError):
        parse_date("2025/05/23")


def test_get_month_range_may() -> None:
    input_date = datetime(2025, 5, 15)
    start, end = get_month_range(input_date)
    assert start == datetime(2025, 5, 1)
    assert end == datetime(2025, 5, 31)


def test_get_month_range_december() -> None:
    input_date = datetime(2025, 12, 10)
    start, end = get_month_range(input_date)
    assert start == datetime(2025, 12, 1)
    assert end == datetime(2025, 12, 31)


def test_get_period_start_week() -> None:
    end_date = datetime(2025, 5, 23)
    result = get_period_start(end_date, "W")
    assert result == datetime(2025, 5, 17)


def test_get_period_start_month() -> None:
    end_date = datetime(2025, 5, 23)
    result = get_period_start(end_date, "M")
    assert result == datetime(2025, 5, 1)


def test_get_period_start_year() -> None:
    end_date = datetime(2025, 5, 23)
    result = get_period_start(end_date, "Y")
    assert result == datetime(2025, 1, 1)


def test_get_period_start_all() -> None:
    end_date = datetime(2025, 5, 23)
    result = get_period_start(end_date, "ALL")
    assert result == datetime(2000, 1, 1)


def test_get_period_start_unknown_defaults_to_month() -> None:
    end_date = datetime(2025, 5, 23)
    result = get_period_start(end_date, "???")
    assert result == datetime(2025, 5, 1)


@pytest.mark.parametrize(
    "hour,expected",
    [
        (6, "Доброе утро"),
        (11, "Доброе утро"),
        (12, "Добрый день"),
        (17, "Добрый день"),
        (18, "Добрый вечер"),
        (22, "Добрый вечер"),
        (0, "Доброй ночи"),
        (4, "Доброй ночи"),
    ],
)
def test_get_greeting(hour: int, expected: str) -> None:
    dt = datetime(2025, 5, 23, hour, 0, 0)
    assert get_greeting(dt) == expected
