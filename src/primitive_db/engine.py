import shlex

import prompt

from primitive_db.constants import META_FILE
from primitive_db.core import create_table, drop_table, list_tables
from primitive_db.utils import load_metadata, save_metadata


def print_help():
    """Показать доступные команды базы данных."""
    print("\n***База данных***")
    print("create_table <имя> <столбец:тип> ... - создать таблицу")
    print("drop_table <имя> - удалить таблицу")
    print("list_tables - показать список таблиц")
    print("help - справочная информация")
    print("exit - выйти\n")


def execute_command(metadata, args):
    """Выполнить команду и вернуть False, если пользователь выбрал выход."""
    command = args[0]
    arguments = args[1:]
    invalid_value = " ".join(args)
    argument_error = f"Некорректное значение: {invalid_value}. Попробуйте снова."

    if command == "create_table":
        if len(arguments) < 2:
            raise ValueError(argument_error)

        table_name = arguments[0]
        existed_before = table_name in metadata
        create_table(metadata, table_name, arguments[1:])

        if not existed_before and table_name in metadata:
            save_metadata(META_FILE, metadata)

    elif command == "drop_table":
        if len(arguments) != 1:
            raise ValueError(argument_error)

        table_name = arguments[0]
        existed_before = table_name in metadata
        drop_table(metadata, table_name)

        if existed_before and table_name not in metadata:
            save_metadata(META_FILE, metadata)

    elif command in {"list_tables", "help", "exit"}:
        if arguments:
            raise ValueError(argument_error)

        if command == "list_tables":
            table_names = list_tables(metadata)
            if not table_names:
                print("Таблиц пока нет.")
            for table_name in table_names:
                print(f"- {table_name}")
        elif command == "help":
            print_help()
        else:
            return False

    else:
        print(f"Функции {command} нет. Попробуйте снова.")

    return True


def run():
    """Запустить цикл ввода команд и сохранять успешные изменения."""
    print_help()

    while True:
        try:
            metadata = load_metadata(META_FILE)
            if not isinstance(metadata, dict):
                raise ValueError("Метаданные должны быть словарём.")
        except (OSError, ValueError) as error:
            print(f"Ошибка чтения метаданных: {error}")
            return

        try:
            user_input = prompt.string("Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            print("\nРабота завершена.")
            return

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

        if not args:
            continue

        try:
            if not execute_command(metadata, args):
                return
        except ValueError as error:
            print(error)
        except OSError as error:
            print(f"Ошибка сохранения: {error}. Изменения не записаны на диск.")
