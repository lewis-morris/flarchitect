from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from flask import Response, request
from sqlalchemy.exc import ProgrammingError
from werkzeug.exceptions import HTTPException

from flarchitect.exceptions import CustomHTTPException
from flarchitect.exceptions import _handle_exception as _handle_exception
from flarchitect.schemas.utils import deserialise_data
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.core_utils import convert_case
from flarchitect.utils.general import HTTP_BAD_REQUEST, HTTP_INTERNAL_SERVER_ERROR
from flarchitect.utils.response_helpers import create_response
from flarchitect.utils.responses import serialise_output_with_mallow

if TYPE_CHECKING:  # pragma: no cover - used only for type checking
    from flarchitect.schemas.bases import AutoSchema


def add_dict_to_query(f: Callable) -> Callable:
    """Add a ``dictionary`` key to outputs containing SQLAlchemy row objects.

    Why/How:
        Custom queries often return Core row objects rather than ORM models.
        This wrapper converts those rows to plain dictionaries under
        ``output["dictionary"]`` to make serialisation and testing easier.

    Returns:
        Decorated function that augments the result payload when applicable.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        output = f(*args, **kwargs)
        if isinstance(output, dict):
            try:
                if isinstance(output["query"], list):
                    output["dictionary"] = [result._asdict() for result in output["query"]]
                else:
                    output["dictionary"] = output["query"]._asdict()
            except AttributeError:
                pass
        return output

    return decorated_function


def add_page_totals_and_urls(f: Callable) -> Callable:
    """Attach pagination totals and navigation URLs to a result payload.

    Why/How:
        Uses the current request URL and the returned ``page``, ``limit`` and
        ``total_count`` values to calculate ``next_url``, ``previous_url``,
        ``current_page`` and ``total_pages``.

    Args:
        f: Function to decorate.

    Returns:
        Decorated function with pagination keys added when possible.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        output = f(*args, **kwargs)
        limit, page, total_count = (
            output.get("limit"),
            output.get("page"),
            output.get("total_count"),
        )

        next_url, previous_url, current_page, total_pages = None, None, None, None

        if total_count and limit:
            total_pages = -(-total_count // limit)  # Ceiling division
            current_page = page

            parsed_url = urlparse(request.url)
            query_params = parse_qs(parsed_url.query)

            query_params["limit"] = [str(limit)]
            next_page, prev_page = page + 1, page - 1
            next_url = _construct_url(parsed_url, query_params, next_page, total_count, limit)
            previous_url = _construct_url(parsed_url, query_params, prev_page, total_count, limit)

        if isinstance(output, dict):
            output.update(
                {
                    "next_url": next_url,
                    "previous_url": previous_url,
                    "current_page": current_page,
                    "total_pages": total_pages,
                }
            )

        return output

    return decorated_function


def _construct_url(parsed_url, query_params, page, total_count, limit):
    """Construct a pagination URL for a specific page if within bounds.

    Args:
        parsed_url: Parsed URL tuple from :func:`urllib.parse.urlparse`.
        query_params: Mapping of query parameters to encode.
        page: Target page number.
        total_count: Total number of items.
        limit: Items per page.

    Returns:
        The constructed URL string or ``None`` if out of range.
    """
    if 0 < page <= total_count // limit:
        query_params["page"] = [str(page)]
        return urlunparse(parsed_url._replace(query=urlencode(query_params, doseq=True)))
    return None


def handle_many(output_schema: type[AutoSchema] | None, input_schema: type[AutoSchema] | None = None) -> Callable:
    """Serialise a list response and optionally deserialise input.

    Why/How:
        Wraps a route that returns multiple items, applying the supplied
        Marshmallow schema for output and, if provided, validating input via
        ``input_schema``.

    Args:
        output_schema: Marshmallow schema class used to serialise the output.
        input_schema: Optional schema to deserialise request data.

    Returns:
        The decorated function.
    """
    return _handle_decorator(output_schema, input_schema, many=True)


def handle_one(output_schema: type[AutoSchema] | None, input_schema: type[AutoSchema] | None = None) -> Callable:
    """Serialise a single-item response and optionally deserialise input.

    Args:
        output_schema: Marshmallow schema class used to serialise the output.
        input_schema: Optional schema to deserialise request data.

    Returns:
        The decorated function.
    """
    return _handle_decorator(output_schema, input_schema, many=False)


def _handle_decorator(
    output_schema: type[AutoSchema] | None,
    input_schema: type[AutoSchema] | None,
    many: bool,
) -> Callable:
    """Base decorator to handle input and output using Marshmallow schemas.

    Args:
        output_schema: Schema used to serialise output.
        input_schema: Schema used to deserialise input.
        many: Whether the route returns multiple records.

    Returns:
        The decorated function.
    """

    def decorator(func: Callable) -> Callable:
        # Core logic shared by both branches (with/without fields wrapper)
        def _core(*args: Any, **kwargs: dict[str, Any]) -> dict[str, Any] | tuple:
            if input_schema:
                data_or_error = deserialise_data(input_schema, request)
                if isinstance(data_or_error, tuple):  # Error occurred during deserialisation
                    case = get_config_or_model_meta("API_FIELD_CASE", default="snake")
                    error = {convert_case(k, case): v for k, v in data_or_error[0].items()}
                    raise CustomHTTPException(HTTP_BAD_REQUEST, error)
                kwargs["deserialized_data"] = data_or_error
                kwargs["model"] = getattr(input_schema.Meta, "model", None)

            # Extract any schema injected by fields() so it isn't passed to func
            new_output_schema: type[AutoSchema] | None = kwargs.pop("schema", None)

            # Filter kwargs to only those accepted by the target function. If
            # the target accepts ``**kwargs`` forward the full mapping so
            # decorator-injected helpers (e.g. route factories) retain access
            # to values like ``deserialized_data`` and ``model``.
            import inspect as _inspect

            sig = _inspect.signature(func)
            accepts_var_kwargs = any(param.kind == _inspect.Parameter.VAR_KEYWORD for param in sig.parameters.values())
            accepted = set(sig.parameters.keys())

            filtered_kwargs = dict(kwargs) if accepts_var_kwargs else {k: v for k, v in kwargs.items() if k in accepted}

            result = func(*args, **filtered_kwargs)
            return serialise_output_with_mallow(new_output_schema, result) if new_output_schema else result

        # Assemble wrapper with or without the fields() decorator
        if output_schema is not None:
            @wraps(func)
            @standardise_response
            @fields(output_schema, many=many)
            def wrapper(*args: Any, **kwargs: dict[str, Any]) -> dict[str, Any] | tuple:
                return _core(*args, **kwargs)
        else:
            @wraps(func)
            @standardise_response
            def wrapper(*args: Any, **kwargs: dict[str, Any]) -> dict[str, Any] | tuple:
                return _core(*args, **kwargs)

        return wrapper

    return decorator


def _response_from_result(result: Any) -> Response:
    if isinstance(result, Response):
        return result

    if isinstance(result, tuple) and result and isinstance(result[0], Response):
        response = result[0]
        if len(result) > 1 and isinstance(result[1], int):
            response.status_code = result[1]
        return response

    return create_response(result=result)


def _response_payload(response: Response) -> dict[str, Any]:
    payload = response.get_json(silent=True) or {}
    return payload if isinstance(payload, dict) else {}


def _response_error_state(response: Response) -> tuple[bool, Any | None, int | None, Any | None]:
    status_code = response.status_code
    payload = _response_payload(response)
    error_payload = payload.get("errors")
    value = payload.get("value")
    return error_payload is not None or status_code >= 400, error_payload, status_code, value


def _programming_error_text(error: ProgrammingError) -> str:
    message = str(error)
    _, separator, remainder = message.partition(")")
    text = remainder if separator else message
    return text.split("\n", 1)[0].strip().capitalize()


def _exception_response(error: Exception) -> tuple[Response, Any | None, int | None]:
    if isinstance(error, HTTPException):
        status_code = error.code or HTTP_INTERNAL_SERVER_ERROR
        response = _handle_exception(error.description, status_code, error.name, print_exc=True)
    elif isinstance(error, ProgrammingError):
        status_code = HTTP_BAD_REQUEST
        response = _handle_exception(f"SQL Format Error: {_programming_error_text(error)}", status_code)
    elif isinstance(error, CustomHTTPException):
        status_code = error.status_code
        response = _handle_exception(error.reason, status_code, error.error)
    else:
        status_code = HTTP_INTERNAL_SERVER_ERROR
        response = _handle_exception(f"Internal Server Error: {error}", status_code)

    return response, _response_payload(response).get("errors"), status_code


def _trigger_error_callback(error_payload: Any | None, status_code: int | None, value: Any | None) -> None:
    error_callback = get_config_or_model_meta("API_ERROR_CALLBACK")
    if error_callback:
        error_callback(error_payload, status_code, value)


def standardise_response(func: Callable) -> Callable:
    """Standardise API responses and trigger error callbacks consistently.

    Why/How:
        Ensures responses follow a uniform envelope via
        :func:`flarchitect.utils.response_helpers.create_response`, catches
        common exceptions and routes them through a central handler, then calls
        any configured error callback.

    Args:
        func: The route handler to wrap.

    Returns:
        A wrapper that returns a :class:`flask.Response`.
    """

    @wraps(func)
    def decorated_function(*args: Any, **kwargs: Any) -> Response:
        had_error = False
        error_payload: Any | None = None
        status_code: int | None = None
        value: Any | None = None

        try:
            out_resp = _response_from_result(func(*args, **kwargs))
            had_error, error_payload, status_code, value = _response_error_state(out_resp)
        except Exception as e:
            had_error = True
            value = None
            out_resp, error_payload, status_code = _exception_response(e)

        finally:
            if had_error:
                _trigger_error_callback(error_payload, status_code, value)

        return out_resp

    return decorated_function


# Backwards-compatible alias (US spelling)
def standardize_response(func: Callable) -> Callable:  # pragma: no cover - shim
    return standardise_response(func)


def fields(model_schema: type[AutoSchema] | None, many: bool = False) -> Callable:
    """Control which fields are serialised on the response.

    Why/How:
        Reads an optional ``fields`` query parameter and re-instantiates the
        output schema with ``only`` to reduce payload size. Falls back to the
        full schema when the parameter is absent.

    Args:
        model_schema: Marshmallow schema class for the response.
        many: Whether the endpoint returns a collection.

    Returns:
        The decorated function.
    """

    # If no schema provided, return a no-op decorator
    if model_schema is None:
        def _noop(func: Callable) -> Callable:
            return func

        return _noop

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: dict[str, Any]) -> Any:
            if request.method == "DELETE":
                return func(*args, **kwargs)

            select_fields = request.args.get("fields")
            if select_fields and get_config_or_model_meta("API_ALLOW_SELECT_FIELDS", model_schema.Meta.model, default=True):
                requested = [field.split(".")[-1] for field in select_fields.split(",")]
                # Only pass fields that actually exist on the schema to avoid KeyErrors
                try:
                    available = set((model_schema().fields.keys()) if callable(model_schema) else model_schema.fields.keys())
                except Exception:
                    available = set()
                filtered = [f for f in requested if f in available]
                if callable(model_schema):
                    kwargs["schema"] = model_schema(many=many, only=filtered) if filtered else model_schema(many=many)
                else:
                    kwargs["schema"] = model_schema.__class__(many=many, only=filtered) if filtered else model_schema.__class__(many=many)
            else:
                if callable(model_schema):
                    kwargs["schema"] = model_schema(many=many)
                else:
                    kwargs["schema"] = model_schema.__class__(many=many)

            return func(*args, **kwargs)

        return wrapper

    return decorator
