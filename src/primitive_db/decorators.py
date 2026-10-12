import time

import prompt


def _preserve_metadata(wrapper, func):
    """Перенести описание исходной функции на обёртку без сторонних модулей."""
    attributes = (
        "__name__",
        "__qualname__",
        "__doc__",
        "__module__",
        "__annotations__",
    )
    for attribute in attributes:
        if hasattr(func, attribute):
            setattr(wrapper, attribute, getattr(func, attribute))
    wrapper.__dict__.update(getattr(func, "__dict__", {}))
    wrapper.__wrapped__ = func
    return wrapper


def handle_db_errors(func):
    """Обработать ошибки базы данных, вернув None при неудачной операции."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден. Возможно, база не инициализирована.")
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")
        except OSError as error:
            print(f"Ошибка работы с файлами: {error}")
        except Exception as error:
            print(f"Произошла непредвиденная ошибка: {error}")
        return None

    return _preserve_metadata(wrapper, func)


def confirm_action(action_name):
    """Запросить подтверждение перед выполнением указанной операции."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                answer = prompt.string(
                    f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]:',
                    empty=True,
                )
            except (EOFError, KeyboardInterrupt):
                print("\nОперация отменена.")
                return None

            if answer is None or answer.strip().lower() != "y":
                print("Операция отменена.")
                return None
            return func(*args, **kwargs)

        return _preserve_metadata(wrapper, func)

    return decorator


def log_time(func):
    """Показать время выполнения функции, в том числе при возникновении ошибки."""

    def wrapper(*args, **kwargs):
        started_at = time.monotonic()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = time.monotonic() - started_at
            print(f"Функция {func.__name__} выполнилась за {elapsed:.3f} секунд")

    return _preserve_metadata(wrapper, func)


def create_cacher():
    """Создать функцию кэширования с отдельным словарём в замыкании."""
    cache = {}

    def cache_result(key, value_func):
        """Вернуть сохранённый результат или вычислить и запомнить новый."""
        if key not in cache:
            cache[key] = value_func()
        return cache[key]

    cache_result.clear = cache.clear
    return cache_result
