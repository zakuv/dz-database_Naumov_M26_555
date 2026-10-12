TYPE_CLASSES = {"int": int, "str": str, "bool": bool}
VALID_TYPES = set(TYPE_CLASSES)
ID_NAME = "ID"
ID_COLUMN = f"{ID_NAME}:int"
META_FILE = "db_meta.json"
DATA_DIR = "data"
COMMAND_PROMPT = "Введите команду: "
TABLE_COMMANDS = {"create_table", "drop_table", "list_tables"}
CRUD_COMMANDS = {"insert", "select", "update", "delete", "info"}
HELP_TEXT = (
    "\n***База данных***\n\n"
    "Управление таблицами:\n"
    "create_table <имя> <столбец:тип> ... - создать таблицу\n"
    "drop_table <имя> - удалить таблицу\n"
    "list_tables - показать список таблиц\n\n"
    "Операции с данными:\n"
    "insert into <таблица> values (<значение>, ...) - добавить запись\n"
    "select from <таблица> [where <столбец> = <значение>] - выбрать записи\n"
    "update <таблица> set <столбец> = <значение> "
    "where <столбец> = <значение> - обновить записи\n"
    "delete from <таблица> where <столбец> = <значение> - удалить записи\n"
    "info <таблица> - информация о таблице\n\n"
    "Общие команды:\n"
    "help - справочная информация\n"
    "exit - выйти\n"
)
