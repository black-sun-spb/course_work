# src/decorators.py

import functools


def save_result_to_file(filename):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # Предполагается, что результат — это JSON-строка
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(result)
            return result
        return wrapper
    return decorator
