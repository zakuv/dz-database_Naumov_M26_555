import json
import shlex

from primitive_db.constants import TYPE_CLASSES


def parse_value(text):
    """Преобразовать строковый литерал в str, int или bool."""
    text = text.strip()
    if not text:
        raise ValueError("Значение не может быть пропущено.")

    if text.startswith("'"):
        tokens = shlex.split(text, posix=False)
        if len(tokens) != 1 or tokens[0] != text or not text.endswith("'"):
            raise ValueError(f"Некорректное строковое значение: {text}")
        return shlex.split(text)[0]

    if text.lower() == "true":
        return True
    if text.lower() == "false":
        return False

    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"Некорректное значение: {text}. Строки заключайте в кавычки."
        ) from error

    if type(value) not in TYPE_CLASSES.values():
        raise ValueError(f"Некорректное значение: {text}. Допустимы int, str, bool.")
    return value


def _outside_positions(text):
    """Вернуть позиции символов вне строк, проверив закрытие кавычек."""
    quote = None
    escaped = False

    for position, character in enumerate(text):
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\" and quote == '"':
                escaped = True
            elif character == quote:
                quote = None
        elif character in {"'", '"'}:
            quote = character
        else:
            yield position

    if quote is not None:
        raise ValueError("Незакрытые кавычки в значении.")


def _split_outside_quotes(text, separator):
    """Разделить текст по символу, сохраняя разделители внутри строк."""
    parts = []
    start = 0
    for position in _outside_positions(text):
        if text[position] == separator:
            parts.append(text[start:position].strip())
            start = position + 1

    parts.append(text[start:].strip())
    return parts


def _parse_assignment(text):
    """Разобрать одну пару вида столбец = значение."""
    parts = _split_outside_quotes(text, "=")
    if len(parts) != 2 or not parts[0]:
        raise ValueError(f"Некорректное условие: {text}. Формат: столбец = значение.")
    column_name, value_text = parts
    if column_name.startswith(("'", '"')):
        column_name = parse_value(column_name)
    elif any(character.isspace() for character in column_name):
        raise ValueError("Имена столбцов с пробелами заключайте в кавычки.")
    if not isinstance(column_name, str) or not column_name.strip():
        raise ValueError("Имя столбца должно быть непустой строкой.")
    return column_name, parse_value(value_text)


def parse_values(text):
    """Разобрать список values в скобках, сохранив тип каждого значения."""
    text = text.strip()
    if not text.startswith("(") or not text.endswith(")"):
        raise ValueError("Значения должны быть перечислены в круглых скобках.")

    content = text[1:-1].strip()
    if not content:
        return []

    return [parse_value(part) for part in _split_outside_quotes(content, ",")]


def parse_where(text):
    """Разобрать одно условие where в словарь вида {столбец: значение}."""
    column_name, value = _parse_assignment(text)
    return {column_name: value}


def parse_set(text):
    """Разобрать одно или несколько присваиваний set, разделённых запятыми."""
    updates = {}
    for assignment in _split_outside_quotes(text, ","):
        column_name, value = _parse_assignment(assignment)
        if column_name in updates:
            raise ValueError(f'Столбец "{column_name}" указан в set повторно.')
        updates[column_name] = value
    return updates


def _tokenize_command(text):
    """Выделить сырые токены с позициями, сохранив кавычки и экранирование."""
    outside_positions = set(_outside_positions(text))
    tokens = []
    start = None

    for position, character in enumerate(text):
        is_separator = position in outside_positions and (
            character.isspace() or character in "(),="
        )
        if is_separator:
            if start is not None:
                tokens.append((text[start:position], start, position))
                start = None
            if not character.isspace():
                tokens.append((character, position, position + 1))
        elif start is None:
            start = position

    if start is not None:
        tokens.append((text[start:], start, len(text)))
    return tokens


def _require_keyword(tokens, position, keyword):
    """Проверить обязательное служебное слово без учёта его регистра."""
    if len(tokens) <= position or tokens[position][0].lower() != keyword:
        raise ValueError(f'Ожидается служебное слово "{keyword}".')


def _table_name(tokens, position):
    """Получить имя таблицы из одного токена, разрешив кавычки."""
    if len(tokens) <= position or tokens[position][0] in "(),=":
        raise ValueError("Укажите имя таблицы.")
    names = shlex.split(tokens[position][0])
    if len(names) != 1 or not names[0].strip():
        raise ValueError("Имя таблицы должно быть непустой строкой.")
    return names[0]


def _parse_simple_command(text, command):
    """Разобрать команды управления таблицами и справки через shlex."""
    words = shlex.split(text)
    if words[0].lower() != command:
        raise ValueError(f"Некорректная команда: {text}")
    arguments = words[1:]
    result = {"command": command}

    if command == "create_table":
        if len(arguments) < 2:
            raise ValueError("Формат: create_table <таблица> <столбец:тип> ...")
        result.update(table_name=arguments[0], columns=arguments[1:])
    elif command in {"drop_table", "info"}:
        if len(arguments) != 1:
            raise ValueError(f"Формат: {command} <таблица>")
        result["table_name"] = arguments[0]
    elif arguments:
        raise ValueError(f"Команда {command} не принимает аргументы.")

    return result


def _parse_update(text, tokens):
    """Найти разделитель where, отличив его от одноимённого столбца."""
    _require_keyword(tokens, 2, "set")
    candidates = []

    for token, start, end in tokens[3:]:
        if token.lower() != "where":
            continue
        try:
            set_clause = parse_set(text[tokens[2][2] : start])
            where_clause = parse_where(text[end:])
        except ValueError:
            continue
        candidates.append((set_clause, where_clause))

    if len(candidates) != 1:
        raise ValueError("Формат: update <таблица> set <поля> where <условие>")
    set_clause, where_clause = candidates[0]
    return {
        "command": "update",
        "table_name": _table_name(tokens, 1),
        "set_clause": set_clause,
        "where_clause": where_clause,
    }


def parse_command(text):
    """Разобрать команду, сохранив исходные строки в values, set и where."""
    tokens = _tokenize_command(text)
    if not tokens:
        return None

    command = tokens[0][0].lower()
    if command in {"create_table", "drop_table", "list_tables", "help", "exit", "info"}:
        return _parse_simple_command(text, command)

    if command == "update":
        return _parse_update(text, tokens)

    if command not in {"insert", "select", "delete"}:
        return {"command": command}

    _require_keyword(tokens, 1, "into" if command == "insert" else "from")
    result = {"command": command, "table_name": _table_name(tokens, 2)}

    if command == "insert":
        _require_keyword(tokens, 3, "values")
        result["values"] = parse_values(text[tokens[3][2] :])
    elif command == "select" and len(tokens) == 3:
        result["where_clause"] = None
    else:
        _require_keyword(tokens, 3, "where")
        result["where_clause"] = parse_where(text[tokens[3][2] :])

    return result
