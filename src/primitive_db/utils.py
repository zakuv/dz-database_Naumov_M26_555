import json
import os

from primitive_db.constants import DATA_DIR


def load_metadata(filepath):
    """Загрузить метаданные или вернуть пустой словарь, если файла нет."""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return {}

    if not isinstance(data, dict):
        raise ValueError("Метаданные должны быть JSON-объектом.")
    return data


def save_metadata(filepath, data):
    """Сохранить словарь метаданных в JSON-файл."""
    if not isinstance(data, dict):
        raise ValueError("Метаданные должны быть словарём.")

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def _table_filepath(table_name):
    """Получить путь файла таблицы без вложенных каталогов в её имени."""
    if (
        not isinstance(table_name, str)
        or not table_name.strip()
        or table_name in {".", ".."}
        or "/" in table_name
        or "\\" in table_name
    ):
        raise ValueError("Имя таблицы должно быть непустым и без разделителей пути.")
    return os.path.join(DATA_DIR, f"{table_name}.json")


def _validate_table_data(data):
    """Проверить, что данные таблицы являются списком словарей."""
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError("Данные таблицы должны быть списком словарей.")


def load_table_data(table_name):
    """Загрузить записи таблицы или вернуть пустой список, если файла нет."""
    filepath = _table_filepath(table_name)
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []

    _validate_table_data(data)
    return data


def save_table_data(table_name, data):
    """Сохранить список записей таблицы, при необходимости создав data/."""
    filepath = _table_filepath(table_name)
    _validate_table_data(data)
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
