from primitive_db.constants import ID_COLUMN, VALID_TYPES


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
