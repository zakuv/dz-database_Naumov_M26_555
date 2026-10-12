import json
import shlex


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

    if type(value) not in (str, int, bool):
        raise ValueError(f"Некорректное значение: {text}. Допустимы int, str, bool.")
    return value


def _split_outside_quotes(text, separator):
    """Разделить текст по символу, сохраняя разделители внутри строк."""
    parts = []
    start = 0
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
        elif character == separator:
            parts.append(text[start:position].strip())
            start = position + 1

    if quote is not None:
        raise ValueError("Незакрытые кавычки в значении.")

    parts.append(text[start:].strip())
    return parts


def _parse_assignment(text):
    """Разобрать одну пару вида столбец = значение."""
    parts = _split_outside_quotes(text, "=")
    if len(parts) != 2 or not parts[0]:
        raise ValueError(f"Некорректное условие: {text}. Формат: столбец = значение.")
    column_name, value_text = parts
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
