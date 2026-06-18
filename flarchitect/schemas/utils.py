from collections.abc import Callable
from typing import Any

from flask import Response, request
from marshmallow import Schema, ValidationError, fields
from sqlalchemy.orm import DeclarativeBase

from flarchitect.database.inspections import extract_model_attributes
from flarchitect.schemas import bases as _schema_bases
from flarchitect.utils.config_helpers import get_config_or_model_meta, is_xml

# Backwards-compatible cache names; tests and callers may monkeypatch these.
_SCHEMA_SUBCLASS_CACHE = _schema_bases._SCHEMA_SUBCLASS_CACHE
_DYNAMIC_SCHEMA_CACHE = _schema_bases._DYNAMIC_SCHEMA_CACHE


def _sync_factory_caches() -> None:
    _schema_bases._SCHEMA_SUBCLASS_CACHE = _SCHEMA_SUBCLASS_CACHE
    _schema_bases._DYNAMIC_SCHEMA_CACHE = _DYNAMIC_SCHEMA_CACHE


def get_schema_subclass(model: Callable, dump: bool | None = False) -> Callable | None:
    _sync_factory_caches()
    return _schema_bases.get_schema_subclass(model, dump=dump)


def create_dynamic_schema(base_class: Callable, model_class: Callable) -> Callable:
    _sync_factory_caches()
    return _schema_bases.create_dynamic_schema(base_class, model_class)


def get_input_output_from_model_or_make(model: Callable, **kwargs) -> tuple[Callable, Callable]:
    _sync_factory_caches()
    return _schema_bases.get_input_output_from_model_or_make(model, **kwargs)


def deserialise_data(input_schema: type[Schema], response: Response) -> dict[str, Any] | tuple[dict[str, Any], int]:
    """Deserialise request data using a Marshmallow schema.

    Why/How:
        Normalises inbound JSON (or XML) against ``input_schema`` and ignores
        relationship fields that arrive as plain strings (for example URLs) so
        PATCH operations can submit previous GET payloads without manual
        sanitisation.

    Args:
        input_schema: Marshmallow schema (class or instance) to validate and
            deserialise with.
        response: Flask response proxy providing the request data.

    Returns:
        The deserialised data on success, or ``(errors, 400)`` on validation
        failure.
    """
    try:
        data = request.data.decode() if is_xml() else response.json

        hook = get_config_or_model_meta("API_GLOBAL_PRE_DESERIALIZE_HOOK", default=None)
        if hook:
            data = hook(data)

        input_schema = (input_schema is not callable(input_schema) and input_schema) or input_schema()

        if hasattr(input_schema, "fields"):
            field_items = {k: v for k, v in input_schema.fields.items() if not v.dump_only}
        else:
            field_items = {k: v for k, v in input_schema._declared_fields.items() if not v.dump_only}

        cleaned: dict[str, Any] = {}
        source_data = data.get("deserialized_data", data)
        for key, value in source_data.items():
            field_obj = field_items.get(key)
            if not field_obj:
                continue
            # ``fields.Nested`` expects a dict (or list for many). When a URL string
            # from a previous GET request is supplied, the field should be ignored
            # to allow partial updates without manual payload pruning.
            if isinstance(field_obj, fields.Nested) and not isinstance(value, (dict | list)):
                continue
            if isinstance(field_obj, fields.List) and isinstance(field_obj.inner, fields.Nested) and not isinstance(value, list):
                continue
            cleaned[key] = value

        data = cleaned
        if request.method == "PATCH":
            from flarchitect.specs.utils import _prepare_patch_schema

            input_schema = _prepare_patch_schema(input_schema)

        try:
            deserialised_data = input_schema().load(data=data)
        except TypeError:
            deserialised_data = input_schema.load(data=data)

        return deserialised_data
    except ValidationError as err:
        return err.messages, 400


# Backwards-compatible alias (US spelling)
def deserialize_data(input_schema: type[Schema], response: Response) -> dict[str, Any] | tuple[dict[str, Any], int]:
    return deserialise_data(input_schema, response)


def filter_keys(model: type[DeclarativeBase], schema: type[Schema], data_dict_list: list[dict]) -> list[dict]:
    """Filter input dictionaries to fields present on the model or schema.

    Why/How:
        Removes unknown keys before deserialisation to keep inputs aligned with
        the model's attributes and declared schema fields.

    Args:
        model: The SQLAlchemy model class.
        schema: The Marshmallow schema class.
        data_dict_list: List of input dictionaries.

    Returns:
        Filtered list of dictionaries.
    """
    model_keys, model_properties = extract_model_attributes(model)
    schema_fields = set(schema._declared_fields.keys())
    all_model_keys = model_keys.union(model_properties)

    return [{key: value for key, value in data_dict.items() if key in all_model_keys or key in schema_fields} for data_dict in data_dict_list]


def dump_schema_if_exists(schema: Schema, data: dict | DeclarativeBase, is_list: bool = False) -> dict[str, Any] | list[dict[str, Any]]:
    """Serialise data with ``schema`` when present.

    Args:
        schema: Marshmallow schema instance to use for serialisation.
        data: Object or dict to serialise.
        is_list: Set True when ``data`` is a list.

    Returns:
        Serialised data, or ``[]``/``None`` when no input is provided.
    """
    return schema.dump(data, many=is_list) if data else ([] if is_list else None)


def list_schema_fields(schema: Schema) -> list[str]:
    """Return field names declared on a Marshmallow schema.

    Args:
        schema: The schema to inspect.

    Returns:
        List of field names.
    """
    return list(schema.fields.keys())
