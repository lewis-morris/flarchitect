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


def handle_many(output_schema: type[AutoSchema], input_schema: type[AutoSchema] | None = None) -> Callable:
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


def handle_one(output_schema: type[AutoSchema], input_schema: type[AutoSchema] | None = None) -> Callable:
    """Serialise a single-item response and optionally deserialise input.

    Args:
        output_schema: Marshmallow schema class used to serialise the output.
        input_schema: Optional schema to deserialise request data.

    Returns:
        The decorated function.
    """
    return _handle_decorator(output_schema, input_schema, many=False)


def _handle_decorator(
    output_schema: type[AutoSchema],
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
        @wraps(func)
        @standardise_response
        @fields(output_schema, many=many)
        def wrapper(*args: Any, **kwargs: dict[str, Any]) -> dict[str, Any] | tuple:
            if input_schema:
                data_or_error = deserialise_data(input_schema, request)
                if isinstance(data_or_error, tuple):  # Error occurred during deserialization
                    case = get_config_or_model_meta("API_FIELD_CASE", default="snake")
                    error = {convert_case(k, case): v for k, v in data_or_error[0].items()}
                    raise CustomHTTPException(HTTP_BAD_REQUEST, error)
                kwargs["deserialized_data"] = data_or_error
                kwargs["model"] = getattr(input_schema.Meta, "model", None)

            new_output_schema: type[AutoSchema] | None = kwargs.pop("schema", None)
            result = func(*args, **kwargs)

            return serialise_output_with_mallow(new_output_schema, result) if new_output_schema else result

        return wrapper

    return decorator


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
        error: Any | None = None
        status_code: int | None = None
        value: Any | None = None

        try:
            result = func(*args, **kwargs)
            out_resp = create_response(result=result)
            status_code = out_resp.status_code
            payload = out_resp.get_json(silent=True) or {}
            value = payload.get("value")
            error = payload.get("errors")
            if error or status_code > 299:
                had_error = True

        except HTTPException as e:
            had_error = True
            error = e.description
            status_code = e.code or HTTP_INTERNAL_SERVER_ERROR
            value = {"error": e.name, "reason": e.description}
            out_resp = _handle_exception(error, status_code, e.name, print_exc=True)

        except ProgrammingError as e:
            had_error = True
            text = str(e).split(")")[1].split("\n")[0].strip().capitalize()
            error = f"SQL Format Error: {text}"
            status_code = HTTP_BAD_REQUEST
            value = None
            out_resp = _handle_exception(error, status_code)

        except CustomHTTPException as e:
            had_error = True
            error = e.reason
            status_code = e.status_code
            value = None
            out_resp = _handle_exception(error, status_code, e.error)

        except Exception as e:
            had_error = True
            error = str(e)
            status_code = HTTP_INTERNAL_SERVER_ERROR
            value = None
            out_resp = _handle_exception(f"Internal Server Error: {error}", status_code)

        finally:
            error_callback = get_config_or_model_meta("API_ERROR_CALLBACK")
            if error_callback and had_error:
                error_callback(error, status_code, value)

        return out_resp

    return decorated_function


# Backwards-compatible alias (US spelling)
def standardize_response(func: Callable) -> Callable:  # pragma: no cover - shim
    return standardise_response(func)


def fields(model_schema: type[AutoSchema], many: bool = False) -> Callable:
    """Control which fields are serialised on the response.

    Why/How:
        Reads an optional ``fields`` query parameter and re‑instantiates the
        output schema with ``only`` to reduce payload size. Falls back to the
        full schema when the parameter is absent.

    Args:
        model_schema: Marshmallow schema class for the response.
        many: Whether the endpoint returns a collection.

    Returns:
        The decorated function.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: dict[str, Any]) -> Any:
            if request.method == "DELETE":
                return func(*args, **kwargs)

            select_fields = request.args.get("fields")
            if select_fields and get_config_or_model_meta("API_ALLOW_SELECT_FIELDS", model_schema.Meta.model, default=True):
                select_fields = [field.split(".")[-1] for field in select_fields.split(",")]
                if callable(model_schema):
                    kwargs["schema"] = model_schema(many=many, only=select_fields)
                else:
                    kwargs["schema"] = model_schema.__class__(many=many, only=select_fields)
            else:
                if callable(model_schema):
                    kwargs["schema"] = model_schema(many=many)
                else:
                    kwargs["schema"] = model_schema.__class__(many=many)

            return func(*args, **kwargs)

        return wrapper

    return decorator
