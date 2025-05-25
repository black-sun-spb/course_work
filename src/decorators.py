# src/decorators.py

import functools
from typing import Callable, Any


def save_result_to_file(filename: str) -> Callable:
    """
    Декоратор, сохраняющий результат функции (JSON-строку) в файл.

    :param filename: Имя файла для сохранения результата
    :return: Обёртка над функцией, сохраняющая результат в файл
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(result)
            return result

        return wrapper

    return decorator
