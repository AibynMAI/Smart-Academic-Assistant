import functools
from datetime import datetime


def log_action(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] ▶ {func.__name__}")
        result = func(*args, **kwargs)
        print(f"[{ts}] ✓ {func.__name__} done")
        return result
    return wrapper