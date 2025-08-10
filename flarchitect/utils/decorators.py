from collections.abc import Callable
from functools import wraps
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from flask import request
from sqlalchemy.exc import ProgrammingError
from werkzeug.exceptions import HTTPException

from flarchitect.exceptions import CustomHTTPException, _handle_exception
from flarchitect.schemas.utils import deserialize_data
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.core_utils import convert_case
from flarchitect.utils.general import (
    HTTP_BAD_REQUEST,
    HTTP_INTERNAL_SERVER_ERROR,
    handle_result,
)
from flarchitect.utils.response_helpers import create_response
from flarchitect.utils.responses import serialize_output_with_mallow


def add_dict_to_query(f: Callable) -> Callable:
    """Decorator that adds a dictionary to the query result.

    This is used when the result is an SQLAlchemy result
    object and not an ORM model, typically in custom queries.

    Returns:
        Callable: Decorated function with additional dictionary in the result.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        output = f(*args, **kwargs)
        if isinstance(output, dict):
            try:
                if isinstance(output["query"], list):
                    output["dictionary"] = [
                        result._asdict() for result in output["query"]
                    ]
                else:
                    output["dictionary"] = output["query"]._asdict()
            except AttributeError:
                pass
        return output

    return decorated_function


def add_page_totals_and_urls(f: Callable) -> Callable:
    """Decorator that adds pagination information (totals and URLs) to the query result.

    Args:
        f (Callable): Function to decorate.

    Returns:
        Callable: Decorated function with pagination information added.
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
            next_url = _construct_url(
                parsed_url, query_params, next_page, total_count, limit
            )
            previous_url = _construct_url(
                parsed_url, query_params, prev_page, total_count, limit
            )

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
    """Helper function to construct next and previous URLs for pagination.

    Args:
        parsed_url: Parsed URL.
        query_params: Query parameters to encode.
        page: The current page number.
        total_count: Total number of items.
        limit: Number of items per page.

    Returns:
        str: Constructed URL.
    """
    if 0 < page <= total_count // limit:
        query_params["page"] = [str(page)]
        return urlunparse(
            parsed_url._replace(query=urlencode(query_params, doseq=True))
        )
    return None


def handle_many(
    output_schema: type["AutoSchema"], input_schema: type["AutoSchema"] | None = None
) -> Callable:
    """
    A decorator to handle multiple records from a route.

    Args:
        output_schema (Schema): The Marshmallow schema to serialize the output.

    Returns:
        Callable: The decorated function.
    """
    return _handle_decorator(output_schema, input_schema, many=True)


def handle_one(
    output_schema: type["AutoSchema"], input_schema: type["AutoSchema"] | None = None
) -> Callable:
    """
    A decorator to handle a single record from a route.

    Args:
        output_schema (Schema): The Marshmallow schema to serialize the output.
        input_schema (Schema, optional): The Marshmallow schema to validate and deserialize input.

    Returns:
        Callable: The decorated function.
    """
    return _handle_decorator(output_schema, input_schema, many=False)


def _handle_decorator(
    output_schema: type["AutoSchema"],
    input_schema: type["AutoSchema"] | None,
    many: bool,
) -> Callable:
    """
    A base decorator to handle input and output using Marshmallow schemas.

    Args:
        output_schema (Schema):
            The Marshmallow schema to serialize output.
        input_schema (Schema, optional):
            The Marshmallow schema to validate and deserialize input.
        many (bool):
            Indicates whether the operation involves multiple records.

    Returns:
        Callable: The decorated function.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @standardize_response
        @fields(output_schema, many=many)
        def wrapper(*args: Any, **kwargs: dict[str, Any]) -> dict[str, Any] | tuple:
            if input_schema:
                data_or_error = deserialize_data(input_schema, request)
                if isinstance(
                    data_or_error, tuple
                ):  # Error occurred during deserialization
                    case = get_config_or_model_meta("API_FIELD_CASE", default="snake")
                    error = {
                        convert_case(k, case): v for k, v in data_or_error[0].items()
                    }
                    raise CustomHTTPException(HTTP_BAD_REQUEST, error)
                kwargs["deserialized_data"] = data_or_error
                kwargs["model"] = getattr(input_schema.Meta, "model", None)

            new_output_schema: type[AutoSchema] | None = kwargs.pop("schema", None)
            result = func(*args, **kwargs)

            return (
                serialize_output_with_mallow(new_output_schema, result)
                if new_output_schema
                else result
            )

        return wrapper

    return decorator


def standardize_response(func: Callable) -> Callable:
    """Standardizes the API response format across all decorated routes."""

    @wraps(func)
    def decorated_function(*args, **kwargs):
        had_error = False

        try:
            result = func(*args, **kwargs)
            status_code, value, count, next_url, previous_url = handle_result(result)
            error = None if status_code < HTTP_BAD_REQUEST else value
            out_resp = create_response(
                value=value if not error else None,
                errors=error,
                status=status_code,
                count=count,
                next_url=next_url,
                previous_url=previous_url,
            )
            if error or status_code > 299:
                had_error = True

        except HTTPException as e:
            had_error = True
            out_resp = _handle_exception(e, e.code, print_exc=True)
        except ProgrammingError as e:
            had_error = True
            text = str(e).split(")")[1].split("\n")[0].strip().capitalize()
            out_resp = _handle_exception(f"SQL Format Error: {text}", HTTP_BAD_REQUEST)
        except CustomHTTPException as e:
            had_error = True
            out_resp = _handle_exception(e.reason, e.status_code, e.error)

        except Exception as e:
            had_error = True
            out_resp = _handle_exception(
                f"Internal Server Error: {str(e)}", HTTP_INTERNAL_SERVER_ERROR
            )
        finally:
            error_callback = get_config_or_model_meta("API_ERROR_CALLBACK")
            # todo check this works and test
            if error_callback and had_error:
                error_callback(error, status_code, value)

        return out_resp

    return decorated_function


def fields(model_schema: type["AutoSchema"], many: bool = False) -> Callable:
    """
    A decorator to specify which fields to return in the response.

    Args:
        model_schema (Type["AutoSchema"]):
            The Marshmallow schema to serialize the output.
        many (bool):
            Indicates whether the operation involves multiple records.

    Returns:
        Callable: The decorated function.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: dict[str, Any]) -> Any:
            select_fields = request.args.get("fields")
            if select_fields and get_config_or_model_meta(
                "API_ALLOW_SELECT_FIELDS", model_schema.Meta.model, default=True
            ):
                select_fields = select_fields.split(",")
                if callable(model_schema):
                    kwargs["schema"] = model_schema(many=many, only=select_fields)
                else:
                    kwargs["schema"] = model_schema.__class__(
                        many=many, only=select_fields
                    )
            else:
                if callable(model_schema):
                    kwargs["schema"] = model_schema(many=many)
                else:
                    kwargs["schema"] = model_schema.__class__(many=many)

            return func(*args, **kwargs)

        return wrapper

    return decorator
