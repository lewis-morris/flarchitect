"""Utilities for serialising and wrapping API responses.

This module provides helper types and functions used to construct consistent
responses throughout the project.  The :class:`CustomResponse` data class allows
endpoints to supply additional pagination metadata that
``create_response`` understands.
"""

from dataclasses import dataclass
from typing import Any

from marshmallow import Schema, ValidationError

from flarchitect.schemas.bases import AutoSchema
from flarchitect.schemas.utils import dump_schema_if_exists
from flarchitect.utils.core_utils import get_count
from flarchitect.utils.general import HTTP_INTERNAL_SERVER_ERROR


@dataclass
class CustomResponse:
    """Container for API response data and pagination metadata.

    Attributes:
        value: The primary payload to return to the client.
        next_url: Link to the next page of results, if available.
        previous_url: Link to the previous page of results, if available.
        count: Total number of objects available.
    """

    value: Any
    next_url: str | None = None
    previous_url: str | None = None
    count: int | None = None


def serialise_output_with_mallow(output_schema: type[Schema], data: Any) -> dict[str, Any] | tuple[dict[str, Any], int]:
    """Serialise ``data`` using the provided Marshmallow schema.

    Args:
        output_schema: The Marshmallow schema to be used for serialisation.
        data: The data to be serialised.

    Returns:
        dict[str, Any] | tuple[dict[str, Any], int]:
            The serialised payload ready for :func:`handle_result`. If
            validation fails a tuple of ``(errors, status_code)`` is returned.
    """

    try:
        is_list = isinstance(data, list) or (isinstance(data, dict) and ("value" in data or ("query" in data and isinstance(data["query"], list))))
        dump_data = data.get("query", data) if isinstance(data, dict) else data
        value = dump_schema_if_exists(output_schema, dump_data, is_list)
        count = get_count(data, value)
        return {
            "query": value,
            "total_count": count,
            "next_url": data.get("next_url") if isinstance(data, dict) else None,
            "previous_url": data.get("previous_url") if isinstance(data, dict) else None,
        }

    except ValidationError as err:
        return {"errors": err.messages}, HTTP_INTERNAL_SERVER_ERROR


def check_serialise_method_and_return(
    result: dict,
    schema: AutoSchema,
    model_columns: list[str],
    schema_columns: list[str],
) -> list[dict[str, Any]] | dict[str, Any]:
    """
    Checks if the serialisation matches the schema or model columns.
    If not, returns the raw result.

    Args:
        result (Dict): The result dictionary.
        schema (AutoSchema): The schema used for serialisation.
        model_columns (List[str]): The model columns.
        schema_columns (List[str]): The schema columns.

    Returns:
        list[dict[str, Any]] | dict[str, Any]:
            Serialised data or the original result.
    """
    output_list = result.pop("dictionary", [])
    if output_list:
        output_keys = list(output_list[0].keys())
        if any(x not in model_columns for x in output_keys) or any(x not in schema_columns for x in output_keys):
            return output_list

    return serialise_output_with_mallow(schema, result)


# Backwards-compatible alias (US spelling)
def serialize_output_with_mallow(output_schema: type[Schema], data: Any) -> dict[str, Any] | tuple[dict[str, Any], int]:
    return serialise_output_with_mallow(output_schema, data)
