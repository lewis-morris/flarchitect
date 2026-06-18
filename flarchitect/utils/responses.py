"""Utilities for serialising and wrapping API responses.

This module provides helper types and functions used to construct consistent
responses throughout the project.  The :class:`CustomResponse` data class allows
endpoints to supply additional pagination metadata that
``create_response`` understands.
"""

from dataclasses import dataclass
from typing import Any

from marshmallow import Schema, ValidationError

from flarchitect.database.utils import list_model_columns
from flarchitect.schemas.bases import AutoSchema
from flarchitect.schemas.utils import dump_schema_if_exists, list_schema_fields
from flarchitect.utils.core_utils import get_count
from flarchitect.utils.general import HTTP_UNPROCESSABLE_ENTITY


def _flatten_validation_messages(messages: Any) -> dict[str, list[str]]:
    """Collapse nested Marshmallow error messages into a simple field mapping."""

    flattened: dict[str, list[str]] = {}

    if isinstance(messages, dict):
        for key, value in messages.items():
            _flatten_validation_value(flattened, key, value)
        return flattened

    if isinstance(messages, list):
        for item in messages:
            _flatten_validation_value(flattened, "_schema", item)
        return flattened

    if messages is not None:
        flattened.setdefault("_schema", []).append(str(messages))
    return flattened


def _flatten_validation_value(flattened: dict[str, list[str]], key: str, value: Any) -> None:
    if isinstance(value, dict):
        _merge_validation_messages(flattened, _flatten_validation_messages(value))
        return

    if isinstance(value, list):
        for item in value:
            _flatten_validation_value(flattened, key, item)
        return

    flattened.setdefault(key, []).append(str(value))


def _merge_validation_messages(
    target: dict[str, list[str]],
    source: dict[str, list[str]],
) -> None:
    for key, messages in source.items():
        target.setdefault(key, []).extend(messages)


def _is_collection_response(data: Any) -> bool:
    return isinstance(data, list) or (
        isinstance(data, dict) and ("value" in data or ("query" in data and isinstance(data["query"], list)))
    )


def _raw_dictionary_payload_if_needed(
    output_schema: type[Schema],
    data: dict[str, Any],
) -> dict[str, Any] | None:
    dict_list = data.get("dictionary") or []
    if not dict_list:
        return None

    output_keys = list(dict_list[0].keys())
    model = getattr(output_schema, "Meta", None) and getattr(output_schema.Meta, "model", None)
    model_columns = list_model_columns(model) if model else []
    schema_columns = list_schema_fields(output_schema)
    if all(key in model_columns and key in schema_columns for key in output_keys):
        return None

    return {
        "query": dict_list,
        "total_count": get_count(data, dict_list),
        "next_url": data.get("next_url"),
        "previous_url": data.get("previous_url"),
    }


def _response_envelope(data: Any, value: Any) -> dict[str, Any]:
    return {
        "query": value,
        "total_count": get_count(data, value),
        "next_url": data.get("next_url") if isinstance(data, dict) else None,
        "previous_url": data.get("previous_url") if isinstance(data, dict) else None,
    }


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
        is_list = _is_collection_response(data)

        # When the query used with_entities (e.g., selected joined columns),
        # add_dict_to_query may have provided a raw dictionary view under
        # 'dictionary'. If keys extend beyond the schema/model, prefer the raw
        # dictionary so joined fields are preserved.
        if isinstance(data, dict) and "dictionary" in data and output_schema is not None:
            try:
                raw_payload = _raw_dictionary_payload_if_needed(output_schema, data)
                if raw_payload is not None:
                    return raw_payload
            except Exception:
                # Fall through to normal schema dumping on any issue
                pass

        dump_data = data.get("query", data) if isinstance(data, dict) else data
        value = dump_schema_if_exists(output_schema, dump_data, is_list)
        return _response_envelope(data, value)

    except ValidationError as err:
        return {"errors": _flatten_validation_messages(err.messages)}, HTTP_UNPROCESSABLE_ENTITY
    except ValueError as err:
        try:
            schema_instance = output_schema if isinstance(output_schema, Schema) else output_schema()
            load_target = dump_data  # type: ignore[name-defined]
            if isinstance(data, dict) and "query" in data:
                load_target = data["query"]
            try:
                schema_instance.load(load_target, many=is_list)  # type: ignore[arg-type]
            except ValidationError as load_err:
                normalised = _flatten_validation_messages(load_err.messages)
                if normalised:
                    return {"errors": normalised}, HTTP_UNPROCESSABLE_ENTITY
        except Exception:  # pragma: no cover - fallback handling
            pass

        message = "Not a valid integer." if "invalid literal for int()" in str(err) else str(err)
        return {"errors": {"_schema": [message]}}, HTTP_UNPROCESSABLE_ENTITY


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
