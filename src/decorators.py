# src/decorators.py

import functools
import json
import logging
from typing import Any, Callable

import pandas as pd


def save_result_to_file(filename: str) -> Callable:
    """
    Декоратор, сохраняющий результат функции в JSON-файл.
    Поддерживает строки, словари, списки и pandas.DataFrame.

    :param filename: Имя файла для сохранения результата
    :return: Обёртка над функцией
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    if isinstance(result, str):
                        f.write(result)
                    elif isinstance(result, pd.DataFrame):
                        json.dump(result.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
                    else:
                        json.dump(result, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logging.exception(f"Ошибка при сохранении результата в файл {filename}: {e}")
            return result

        return wrapper

    return decorator
