import importlib.util
import os
import pprint
import re
import socket
from collections.abc import Callable
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import inflect
from flask import Flask, current_app
from jinja2 import Environment, FileSystemLoader

from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.core_utils import convert_case, get_count

HTTP_METHODS = ["GET", "POST", "PATCH", "DELETE"]
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
p = inflect.engine()


def get_html_path() -> str:
    """Return the absolute path to the ``html`` templates directory.

    The path is resolved using the registered :class:`~flask.Flask` application
    when available. If the ``flarchitect`` extension is not registered or no
    application context is active, the path is determined by searching for an
    ``html`` folder relative to this file.

    Returns:
        str: Absolute path to the ``html`` directory. Returns an empty string if
        the directory cannot be located.
    """

    try:
        return current_app.extensions["flarchitect"].get_templates_path()  # type: ignore[index]
    except Exception:  # pragma: no cover - fallback when app context not available
        return find_html_directory() or ""


class AttributeInitializerMixin:
    """Used for the base Architect flask extension and others
    to initialise their config attributes."""

    def __init__(self, app: Flask, *args, **kwargs):
        self._set_class_attributes(**kwargs)
        self._set_app_config_attributes(app)
        super().__init__()

    def _set_app_config_attributes(self, app: Flask) -> None:
        """
        Sets class attributes from Flask app config if they exist.

        Args:
            app (Flask): The Flask application instance.
        """
        for key in vars(type(self)):
            if key.startswith("__"):
                continue
            config_key = key.upper().lstrip("_")
            if config_key in app.config:
                setattr(self, key, app.config[config_key])

    def _set_class_attributes(self, **kwargs: Any) -> None:
        """
        Sets class attributes from keyword arguments.

        Args:
            **kwargs: Keyword arguments representing class attributes.
        """
        for key in vars(type(self)):
            if key.startswith("__"):
                continue
            if key in kwargs:
                setattr(self, key, kwargs[key])


class AttributeInitialiserMixin(AttributeInitializerMixin):
    """UK spelling alias of :class:`AttributeInitializerMixin`."""

    pass


def find_html_directory(starting_directory: str | None = None) -> str | None:
    """Locate the nearest ``html`` directory by searching parent folders.

    Args:
        starting_directory: Directory to begin the search from. If ``None``,
            the search starts from the directory containing this module.

    Returns:
        str | None: Absolute path to the ``html`` directory or ``None`` if it
        cannot be found.
    """

    if starting_directory is None:
        starting_directory = os.path.abspath(os.path.dirname(__file__))

    contents = os.listdir(starting_directory)

    if "html" in contents and os.path.isdir(os.path.join(starting_directory, "html")):
        return os.path.join(starting_directory, "html")

    parent_directory = os.path.dirname(starting_directory)
    if starting_directory == parent_directory:
        return None

    return find_html_directory(parent_directory)


def manual_render_absolute_template(absolute_template_path: str, **kwargs: Any) -> str:
    """
    Manually renders a Jinja2 template given an absolute path.

    Args:
        absolute_template_path (str): The absolute path to the template.
        **kwargs: Additional keyword arguments to pass to the template.

    Returns:
        str: The rendered template as a string.
    """

    template_folder = os.path.join(get_html_path(), absolute_template_path)
    if template_folder.endswith(".html"):
        template_folder, template_filename = os.path.split(template_folder)

    env = Environment(loader=FileSystemLoader(template_folder))
    # ensure standard Flask globals like ``url_for`` are available
    try:
        from flask import url_for

        env.globals.update(url_for=url_for)
    except Exception:  # pragma: no cover - fallback when Flask not installed
        pass

    template = env.get_template(template_filename)
    return template.render(**kwargs)


def find_child_from_parent_dir(parent: str, child: str, current_dir: str = os.getcwd()) -> str | None:
    """
    Finds the directory of a child folder within a parent directory.

    Args:
        parent (str): The name of the parent directory.
        child (str): The name of the child directory.
        current_dir (str, optional): The current directory to start the search from.

    Returns:
        Optional[str]: The path to the child directory, or None if not found.
    """
    if os.path.basename(current_dir) == parent:
        for dirname in os.listdir(current_dir):
            if dirname == child:
                return os.path.join(current_dir, dirname)

    for dirname in os.listdir(current_dir):
        if dirname.startswith(".") or dirname == "node_modules":
            continue
        child_dir_path = os.path.join(current_dir, dirname)
        if os.path.isdir(child_dir_path):
            child_dir_path = find_child_from_parent_dir(parent, child, child_dir_path)
            if child_dir_path is not None:
                return child_dir_path

    return None


def check_rate_prerequisites(
    service: str,
    find_spec: Callable[[str], ModuleSpec | None] = importlib.util.find_spec,
) -> None:
    """Verify that dependencies for a cache backend are installed.

    Args:
        service: Name of the cache backend.
        find_spec: Function used to locate module specifications. Allows tests
            to supply a stub without monkeypatching.

    Raises:
        ImportError: If the required client library is missing.
    """
    back_end_spec = "or specify a cache service URI in the flask configuration with the key API_RATE_LIMIT_STORAGE_URI={URL}:{PORT}"
    if service == "Memcached":
        if find_spec("pymemcache") is None:
            raise ImportError("Memcached prerequisite not available. Please install pymemcache " + back_end_spec)
    elif service == "Redis":
        if find_spec("redis") is None:
            raise ImportError("Redis prerequisite not available. Please install redis-py " + back_end_spec)
    elif service == "MongoDB" and find_spec("pymongo") is None:
        raise ImportError("MongoDB prerequisite not available. Please install pymongo " + back_end_spec)


def check_rate_services(
    config_getter: Callable[[str, Any, Any], Any] = get_config_or_model_meta,
    prereq_checker: Callable[[str], None] = check_rate_prerequisites,
    socket_factory: Callable[..., socket.socket] = socket.socket,
) -> str | None:
    """Return the configured or automatically detected rate limit backend.

    Args:
        config_getter: Function used to obtain configuration values.
        prereq_checker: Callable used to validate backend prerequisites.
        socket_factory: Factory returning socket-like objects. Facilitates
            dependency injection for tests without monkeypatching.

    The function accepts explicitly configured cache URIs and validates that the
    scheme corresponds to a supported backend. ``memory://`` is permitted without
    a host component. If no configuration is provided, the function attempts to
    detect running local services for Memcached, Redis, or MongoDB and returns
    the appropriate URI.

    Returns:
        Optional[str]: The URI of the running service, or ``None`` if no service
        is found.
    """
    services = {
        "Memcached": 11211,
        "Redis": 6379,
        "MongoDB": 27017,
    }
    uri = config_getter("API_RATE_LIMIT_STORAGE_URI", default=None)
    if uri:
        parsed = urlparse(uri)
        scheme_map = {
            "memcached": "Memcached",
            "redis": "Redis",
            "mongodb": "MongoDB",
            "memory": None,
        }
        if not parsed.scheme:
            raise ValueError("Rate limit storage URI must include a scheme")
        if parsed.scheme not in scheme_map:
            raise ValueError(f"Unsupported rate limit storage backend: {parsed.scheme}")
        # In-memory backends do not require a network location. All others do.
        if parsed.scheme != "memory" and not parsed.netloc:
            raise ValueError("Rate limit storage URI must include a host")
        service_name = scheme_map[parsed.scheme]
        if service_name:
            prereq_checker(service_name)
        return uri

    # Allow disabling auto-detection in constrained environments (e.g. sandboxes/CI)
    if config_getter("API_RATE_LIMIT_AUTODETECT", default=True) is False:
        return None

    for service, port in services.items():
        try:
            sock = socket_factory(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                sock.connect(("127.0.0.1", port))
                sock.close()
                prereq_checker(service)

                rate_type = {
                    "Memcached": f"memcached://127.0.0.1:{port}",
                    "Redis": f"redis://127.0.0.1:{port}",
                    "MongoDB": f"mongodb://127.0.0.1:{port}",
                }
                return rate_type[service]

            except OSError:
                # Nothing listening on this port; try the next service
                continue
        except PermissionError:
            # Sockets disabled by the runtime (e.g. sandbox). Fall back to in-memory.
            return None

    return None


def validate_flask_limiter_rate_limit_string(rate_limit_str: str) -> bool:
    """
    Validates a rate limit string for Flask-Limiter.

    Args:
        rate_limit_str (str): The rate limit string to validate.

    Returns:
        bool: True if the rate limit string is valid, False otherwise.
    """
    pattern = re.compile(
        r"^\d+\s+per\s+(\d+\s+)?(second|minute|hour|day|seconds|minutes|hours|days)$",
        re.IGNORECASE,
    )
    return bool(pattern.match(rate_limit_str))


def search_all_keys(model: Any, key: str) -> bool:
    """Search for a specific key in all subclasses of a given model.

    Args:
        model (Any): The model class or instance to search in.
        key (str): The key to search for.

    Returns:
        bool: True if the key is found in any subclass, False otherwise.
    """
    return any(any(get_config_or_model_meta(key, model=subclass, method=method) for method in HTTP_METHODS) for subclass in model.__subclasses__())


def generate_readme_html(file_path: str | Path, *args: Any, **kwargs: Any) -> str:
    """Generate README content from a Jinja2 template.

    Args:
        file_path: Path to the Jinja2 template file. Relative paths are
            resolved from the project root.
        *args: Variable length argument list passed to ``render``.
        **kwargs: Arbitrary keyword arguments passed to ``render``.

    Returns:
        Rendered template content.

    Raises:
        FileNotFoundError: If ``file_path`` does not exist.
    """
    path = Path(file_path)
    if not path.is_absolute():
        # Resolve relative paths from the project root to avoid dependence on
        # the current working directory during test execution.
        path = Path(__file__).resolve().parents[2] / path

    if not path.exists():
        raise FileNotFoundError(f"{path} not found.")

    environment = Environment(loader=FileSystemLoader(str(path.parent)))
    template = environment.get_template(path.name)
    return template.render(*args, **kwargs)


def read_file_content(path: str) -> str:
    """Get the content of a file.

    Args:
        path (str): The path to the file.

    Returns:
        str: The content of the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if os.path.exists(path):
        with open(path) as file:
            return file.read()
    raise FileNotFoundError(f"{path} not found.")


def case_no_change(s: str) -> str:
    """Return the input string unchanged.

    Args:
        s (str): The input string.

    Returns:
        str: The same input string.
    """
    return s


def pretty_print_dict(d: dict[Any, Any]) -> str:
    """Pretty print a dictionary.

    Args:
        d (Dict[Any, Any]): The dictionary to pretty print.

    Returns:
        str: The pretty-printed dictionary.
    """
    return pprint.pformat(d, indent=2)


def update_dict_if_flag_true(output: dict[str, Any], flag: bool, key: str, value: Any, case_func: Any) -> None:
    """Update a dictionary with a key-value pair if the flag is True.

    Args:
        output (Dict[str, Any]): The dictionary to update.
        flag (bool): The flag that controls whether to update.
        key (str): The key to update in the dictionary.
        value (Any): The value to associate with the key.
        case_func (Any): The function to convert the case of the key.
    """
    if flag:
        output.update({convert_case(key, case_func): value})


def make_base_dict() -> dict[str, Any]:
    """Create a base dictionary with configuration settings.

    Returns:
        Dict[str, Any]: The base dictionary with configuration settings.
    """
    output = {"value": "..."}
    # Default to 'snake' which is recognised by convert_case
    field_case = get_config_or_model_meta("API_FIELD_CASE", default="snake")

    config_options = [
        ("API_DUMP_DATETIME", "datetime", "2024-01-01T00:00:00.0000+00:00"),
        (
            "API_DUMP_VERSION",
            "api_version",
            get_config_or_model_meta("API_VERSION", default=True),
        ),
        ("API_DUMP_STATUS_CODE", "status_code", 200),
        ("API_DUMP_RESPONSE_MS", "response_ms", 15),
        ("API_DUMP_TOTAL_COUNT", "total_count", 10),
        ("API_DUMP_NULL_NEXT_URL", "next_url", "/api/example/url"),
        ("API_DUMP_NULL_PREVIOUS_URL", "previous_url", "null"),
        ("API_DUMP_NULL_ERRORS", "errors", "null", False),
    ]

    for config, key, value, *defaults in config_options:
        flag = get_config_or_model_meta(config, default=defaults[0] if defaults else True)
        update_dict_if_flag_true(output, flag, key, value, field_case)

    return output


def pluralize_last_word(converted_name: str) -> str:
    """
    Pluralize the last word of the converted name
    while preserving the rest of the name and its case.

    Args:
        converted_name (str): The name after case conversion.

    Returns:
        str: The name with the last word pluralized.
    """
    delimiters = {"_": "snake", "-": "kebab"}
    delimiter = next((d for d in delimiters if d in converted_name), "")

    words = converted_name.split(delimiter) if delimiter else re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])", converted_name)
    last_word = words[-1]
    last_word_pluralized = p.plural(p.singular_noun(last_word) or last_word)

    words[-1] = last_word_pluralized
    pluralized_name = delimiter.join(words)

    if delimiters.get(delimiter) in ["screaming_snake", "screaming_kebab"]:
        pluralized_name = pluralized_name.upper()

    return pluralized_name


def normalize_key(key: str) -> str:
    """
    Converts a key to uppercase.

    Args:
        key (str): The key to be normalized.

    Returns:
        str: The normalized key.
    """
    return key.upper()


def xml_to_dict(xml_data: str | bytes) -> dict[str, Any]:
    """
    Converts an XML string or bytes into a dictionary.
    Args:
        xml_data (Union[str, bytes]): The XML data.
    Returns:
        Dict[str, Any]: The resulting dictionary.
    """
    xml_data = xml_data.decode() if hasattr(xml_data, "decode") else xml_data

    def element_to_dict(element: ET.Element) -> Any:
        if not list(element) and (element.text is None or not element.text.strip()):
            return None
        if element.text and element.text.strip() and not list(element):
            return element.text.strip()
        result = {}
        for child in element:
            child_result = element_to_dict(child)
            if child.tag not in result:
                result[child.tag] = child_result
            else:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_result)
        return result

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        raise ValueError("Invalid XML data provided") from e
    return {root.tag: element_to_dict(root)}


def handle_result(result: Any) -> tuple[int, Any, int, str | None, str | None]:
    """Normalise values returned from route handlers.

    Args:
        result: The value returned by a view function. It may be a
            raw value, a ``(value, status_code)`` tuple or a dictionary
            containing ``query`` and pagination metadata.

    Returns:
        tuple[int, Any, int, str | None, str | None]:
            A tuple of ``(status_code, value, count, next_url, previous_url)``
            ready for ``create_response``.
    """

    status_code, value, count, next_url, previous_url = HTTP_OK, result, 1, None, None

    if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], int):
        result, status_code = result
    if isinstance(result, dict):
        value = result.get("query", result)
        count = get_count(result, value)
        next_url = result.get("next_url")
        previous_url = result.get("previous_url")
    else:
        value = result

    return status_code, value, count, next_url, previous_url


HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
