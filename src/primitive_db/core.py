from primitive_db.constants import ID_COLUMN, ID_NAME, TYPE_CLASSES, VALID_TYPES
from primitive_db.utils import load_table_data


def create_table(metadata, table_name, columns):
    """Проверить структуру и добавить новую таблицу в метаданные."""
    if not table_name.strip():
        print("Некорректное значение: пустое имя таблицы. Попробуйте снова.")
        return metadata

    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    if not columns:
        print("Некорректное значение: список столбцов пуст. Попробуйте снова.")
        return metadata

    id_name, id_type = ID_COLUMN.split(":")
    column_names = set()
    checked_columns = []

    for column in columns:
        parts = column.split(":")

        if len(parts) != 2:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata

        column_name, column_type = parts

        if not column_name.strip() or column_type not in VALID_TYPES:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata

        if column_name in column_names:
            print(f'Ошибка: Столбец "{column_name}" уже указан.')
            return metadata

        if column_name == id_name and column_type != id_type:
            print(f'Ошибка: Столбец "{id_name}" должен иметь тип {id_type}.')
            return metadata

        column_names.add(column_name)

        if column_name != id_name:
            checked_columns.append(column)

    checked_columns.insert(0, ID_COLUMN)
    metadata[table_name] = {"columns": checked_columns}

    print(
        f'Таблица "{table_name}" успешно создана со столбцами: '
        f'{", ".join(checked_columns)}'
    )
    return metadata


def drop_table(metadata, table_name):
    """Удалить существующую таблицу из метаданных."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    del metadata[table_name]
    print(f'Таблица "{table_name}" успешно удалена.')
    return metadata


def list_tables(metadata):
    """Вернуть имена таблиц в алфавитном порядке."""
    return sorted(metadata)


def get_table_schema(metadata, table_name):
    """Получить схему таблицы как словарь имён столбцов и типов Python."""
    if table_name not in metadata:
        raise KeyError(table_name)

    table = metadata[table_name]
    if not isinstance(table, dict):
        raise ValueError(f'Некорректная структура таблицы "{table_name}".')

    columns = table.get("columns")
    if not isinstance(columns, list) or not columns or columns[0] != ID_COLUMN:
        raise ValueError(f'Некорректная структура таблицы "{table_name}".')

    schema = {}
    for column in columns:
        if not isinstance(column, str):
            raise ValueError("Столбцы должны быть строками вида имя:тип.")
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(f"Некорректный столбец: {column}")
        column_name, column_type = parts
        if (
            not column_name.strip()
            or column_type not in TYPE_CLASSES
            or column_name in schema
        ):
            raise ValueError(f"Некорректный столбец: {column}")
        schema[column_name] = TYPE_CLASSES[column_type]
    return schema


def _validate_fields(fields, schema):
    """Проверить имена и точные типы переданных полей."""
    if not isinstance(fields, dict):
        raise ValueError("Поля должны быть переданы словарём.")

    for column_name, value in fields.items():
        if not isinstance(column_name, str) or not column_name.strip():
            raise ValueError("Имя столбца должно быть непустой строкой.")
        if schema is not None and column_name not in schema:
            raise KeyError(column_name)
        if type(value) not in TYPE_CLASSES.values():
            raise ValueError(f'Неподдерживаемый тип значения столбца "{column_name}".')
        if schema is not None and type(value) is not schema[column_name]:
            expected_type = schema[column_name].__name__
            raise ValueError(
                f'Столбец "{column_name}" должен иметь тип {expected_type}.'
            )


def _validate_rows(table_data, schema=None):
    """Проверить записи и уникальные положительные ID; вернуть схему."""
    if not isinstance(table_data, list):
        raise ValueError("Данные таблицы должны быть списком записей.")

    if schema is None and table_data:
        if not isinstance(table_data[0], dict):
            raise ValueError("Записи таблицы должны быть словарями.")
        schema = {name: type(value) for name, value in table_data[0].items()}

    seen_ids = set()
    for row in table_data:
        if not isinstance(row, dict):
            raise ValueError("Записи таблицы должны быть словарями.")
        if schema is not None and set(row) != set(schema):
            raise ValueError("Столбцы записи не соответствуют структуре таблицы.")
        _validate_fields(row, schema)
        if ID_NAME in row:
            row_id = row[ID_NAME]
            if type(row_id) is not int or row_id < 1 or row_id in seen_ids:
                raise ValueError("ID должны быть уникальными положительными числами.")
            seen_ids.add(row_id)
    return schema


def _matches(row, where_clause):
    """Проверить равенство всех условий с учётом точных типов значений."""
    return all(
        type(row[column_name]) is type(value) and row[column_name] == value
        for column_name, value in where_clause.items()
    )


def insert(metadata, table_name, values, table_data=None):
    """Добавить запись с новым ID и вернуть данные для последующего сохранения."""
    schema = get_table_schema(metadata, table_name)
    if table_data is None:
        table_data = load_table_data(table_name)
    _validate_rows(table_data, schema)

    column_names = [name for name in schema if name != ID_NAME]
    if not isinstance(values, (list, tuple)) or len(values) != len(column_names):
        raise ValueError(f"Ожидается значений без ID: {len(column_names)}.")

    fields = dict(zip(column_names, values))
    _validate_fields(fields, schema)
    new_id = max((row[ID_NAME] for row in table_data), default=0) + 1
    row = {ID_NAME: new_id}
    row.update(fields)
    table_data.append(row)
    return table_data


def select(table_data, where_clause=None, schema=None):
    """Вернуть копии всех записей или только записей, подходящих под условие."""
    schema = _validate_rows(table_data, schema)
    if where_clause is None:
        return [row.copy() for row in table_data]

    _validate_fields(where_clause, schema)
    return [row.copy() for row in table_data if _matches(row, where_clause)]


def update(table_data, set_clause, where_clause, schema=None):
    """Обновить все подходящие записи после проверки полей и типов."""
    schema = _validate_rows(table_data, schema)
    _validate_fields(set_clause, schema)
    _validate_fields(where_clause, schema)
    if not set_clause or not where_clause:
        raise ValueError("Для обновления нужны непустые set и where.")
    if ID_NAME in set_clause:
        raise ValueError("ID генерируется автоматически и не изменяется.")

    for row in table_data:
        if _matches(row, where_clause):
            row.update(set_clause)
    return table_data


def delete(table_data, where_clause, schema=None):
    """Удалить все подходящие записи после проверки условия."""
    schema = _validate_rows(table_data, schema)
    _validate_fields(where_clause, schema)
    if not where_clause:
        raise ValueError("Для удаления записей нужно непустое where.")

    table_data[:] = [row for row in table_data if not _matches(row, where_clause)]
    return table_data
