# src/decorators.py

import functools


        @functools.wraps(func)
            result = func(*args, **kwargs)
                f.write(result)
            return result
        return wrapper
    return decorator
