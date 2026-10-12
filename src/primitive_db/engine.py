import prompt
from prettytable import PrettyTable

from primitive_db.constants import (
    COMMAND_PROMPT,
    CRUD_COMMANDS,
    HELP_TEXT,
    ID_NAME,
    META_FILE,
    TABLE_COMMANDS,
)
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    get_table_schema,
    insert,
    list_tables,
    select,
    update,
)
from primitive_db.decorators import handle_db_errors
from primitive_db.parser import parse_command
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    remove_table_data,
    save_metadata,
    save_table_data,
    validate_table_name,
)


def print_help():
    """Показать команды управления таблицами и записями."""
    print(HELP_TEXT)


def print_rows(rows, schema):
    """Вывести записи в PrettyTable в порядке столбцов из метаданных."""
    table = PrettyTable()
    table.field_names = list(schema)
    table.add_rows([[row[column] for column in schema] for row in rows])
    print(table)


def _execute_table_command(metadata, parsed):
    """Выполнить управление таблицами и сохранить успешное изменение."""
    command = parsed["command"]
    if command == "list_tables":
        names = list_tables(metadata)
        if names is None:
            return
        if not names:
            print("Таблиц пока нет.")
        for name in names:
            print(f"- {name}")
        return

    table_name = parsed["table_name"]
    validate_table_name(table_name)
    existed_before = table_name in metadata

    if command == "create_table":
        result = create_table(metadata, table_name, parsed["columns"])
        if result is not None and not existed_before and table_name in metadata:
            save_table_data(table_name, [])
            save_metadata(META_FILE, metadata)
            columns = ", ".join(metadata[table_name]["columns"])
            print(f'Таблица "{table_name}" успешно создана со столбцами: {columns}')
    else:
        if not existed_before:
            print(f'Ошибка: Таблица "{table_name}" не существует.')
            return
        result = drop_table(metadata, table_name)
        if result is not None and existed_before and table_name not in metadata:
            remove_table_data(table_name)
            save_metadata(META_FILE, metadata)
            print(f'Таблица "{table_name}" успешно удалена.')


def _execute_crud_command(metadata, parsed):
    """Выполнить операцию с записями и сохранить успешные изменения."""
    command = parsed["command"]
    table_name = parsed["table_name"]
    schema = get_table_schema(metadata, table_name)
    if schema is None:
        return
    table_data = load_table_data(table_name)

    if command == "insert":
        result = insert(metadata, table_name, parsed["values"], table_data=table_data)
        if result is not None:
            save_table_data(table_name, result)
            new_id = result[-1][ID_NAME]
            print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')

    elif command == "select":
        rows = select(table_data, parsed["where_clause"], schema=schema)
        if rows is not None:
            print_rows(rows, schema)

    elif command in {"update", "delete"}:
        where_clause = parsed["where_clause"]
        affected = select(table_data, where_clause, schema=schema)
        if affected is None:
            return
        if command == "delete" and not affected:
            print("Подходящие записи не найдены.")
            return
        if command == "update":
            result = update(table_data, parsed["set_clause"], where_clause, schema)
        else:
            result = delete(table_data, where_clause, schema)
        if result is None:
            return
        if not affected:
            print("Подходящие записи не найдены.")
            return

        save_table_data(table_name, result)
        for row in affected:
            row_id = row[ID_NAME]
            if command == "update":
                print(
                    f'Запись с ID={row_id} в таблице "{table_name}" успешно обновлена.'
                )
            else:
                print(
                    f'Запись с ID={row_id} успешно удалена из таблицы "{table_name}".'
                )

    elif command == "info":
        rows = select(table_data, schema=schema)
        if rows is not None:
            print(f"Таблица: {table_name}")
            print(f"Столбцы: {', '.join(metadata[table_name]['columns'])}")
            print(f"Количество записей: {len(rows)}")


@handle_db_errors
def execute_command(metadata, parsed):
    """Выполнить разобранную команду; вернуть False для выхода."""
    command = parsed["command"]
    if command in TABLE_COMMANDS:
        _execute_table_command(metadata, parsed)
    elif command in CRUD_COMMANDS:
        _execute_crud_command(metadata, parsed)
    elif command == "help":
        print_help()
    elif command == "exit":
        return False
    else:
        print(f"Функции {command} нет. Попробуйте снова.")
    return True


@handle_db_errors
def _load_current_metadata():
    """Прочитать метаданные с общей обработкой ошибок базы данных."""
    return load_metadata(META_FILE)


@handle_db_errors
def _parse_user_input(user_input):
    """Разобрать команду с общей обработкой ошибок ввода."""
    return parse_command(user_input)


def run():
    """Запустить ввод команд с чтением актуальных метаданных в каждом цикле."""
    print_help()
    while True:
        metadata = _load_current_metadata()
        if metadata is None:
            return

        try:
            user_input = prompt.string(COMMAND_PROMPT)
        except (EOFError, KeyboardInterrupt):
            print("\nРабота завершена.")
            return

        parsed = _parse_user_input(user_input)
        if parsed is not None and execute_command(metadata, parsed) is False:
            return
