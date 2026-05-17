def log_action(func):

    def wrapper(*args, **kwargs):

        print(f"\n[LOG] Function '{func.__name__}' started.")

        result = func(*args, **kwargs)

        print(f"[LOG] Function '{func.__name__}' finished.")

        return result

    return wrapper