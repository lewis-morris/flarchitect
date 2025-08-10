"""Core utility helpers for data manipulation."""

import re
from typing import Any

from dicttoxml import dicttoxml


def convert_case(s: str, target_case: str) -> str:
    """
    Convert a string to the specified case format.

    Args:
        s (str): The input string.
        target_case (str):
            The target case format (camel, pascal, snake,
            screaming_snake, kebab, screaming_kebab).

    Returns:
        str: The converted string.
    """
    # Handle empty strings
    if not s:
        return s

    # Regex to handle acronyms and camelCase/PascalCase
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", s)
    words = [word.lower() for word in words]

    # Handle cases where `words` might be empty
    if not words:
        return s

    # Define case converters
    case_converters = {
        "camel": lambda: words[0] + "".join(word.capitalize() for word in words[1:]),
        "pascal": lambda: "".join(word.capitalize() for word in words),
        "snake": lambda: "_".join(words),
        "screaming_snake": lambda: "_".join(word.upper() for word in words),
        "kebab": lambda: "-".join(words),
        "screaming_kebab": lambda: "-".join(word.upper() for word in words),
    }

    # Convert and return the case format
    return case_converters.get(target_case, lambda: s)()


def convert_snake_to_camel(snake_str: str) -> str:
    """
    Convert a snake_case string to camelCase,
    preserving a leading underscore if present.
    """
    leading_underscore = snake_str.startswith("_")
    camel_case_str = convert_case(snake_str, "camel")
    return ("_" if leading_underscore else "") + camel_case_str


def convert_camel_to_snake(camel_str: str) -> str:
    """Convert a camelCase string to snake_case."""
    return convert_case(camel_str, "snake")


def convert_kebab_to_snake(kebab_str: str) -> str:
    """Convert a kebab-case string to snake_case."""
    return convert_case(kebab_str, "snake")


def dict_to_xml(input_dict: dict) -> str:
    """Convert a dictionary to an XML string.

    Args:
        input_dict: Dictionary to be converted.

    Returns:
        str: XML representation of ``input_dict``.
    """

    xml_bytes = dicttoxml(input_dict, custom_root="root", attr_type=False)
    return xml_bytes.decode()


def get_count(result: dict[str, Any], value: Any) -> int:
    """Determine the count of records in the result."""
    if isinstance(result, dict) and result.get("total_count"):
        return result["total_count"]
    return len(value) if isinstance(value, list) else (0 if not value else 1)
