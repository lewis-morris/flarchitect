from collections.abc import Callable
from types import new_class
from typing import Any

from flask import Response, request
from marshmallow import Schema, ValidationError, fields
from sqlalchemy.orm import DeclarativeBase

from flarchitect.database.utils import _extract_model_attributes
from flarchitect.utils.config_helpers import get_config_or_model_meta, is_xml

# Simple module-level caches to avoid repeated reflection per request
_SCHEMA_SUBCLASS_CACHE: dict[tuple[type, bool | None], Callable | None] = {}
_DYNAMIC_SCHEMA_CACHE: dict[tuple[type, type], type] = {}


def get_schema_subclass(model: Callable, dump: bool | None = False) -> Callable | None:
    """Locate an ``AutoSchema`` subclass for a model and usage (dump/load).

    Why/How:
        flarchitect lets you provide bespoke input/output schemas per model by
        subclassing ``AutoSchema``. This helper scans known subclasses and
        returns the one tied to ``model`` and the requested direction
        (``dump`` for output, ``False`` for input).

    Args:
        model: The SQLAlchemy model to match.
        dump: When True, search for an output (dump) schema; when False, for an
            input (load) schema. ``None`` returns any match.

    Returns:
        The matching ``AutoSchema`` subclass if found, otherwise ``None``.
    """
    from flarchitect.schemas.bases import AutoSchema

    if model is None:
        return None

    schema_base = get_config_or_model_meta("API_BASE_SCHEMA", model=model, default=AutoSchema) or AutoSchema

    cache_key = (model, dump)
    if cache_key in _SCHEMA_SUBCLASS_CACHE:
        return _SCHEMA_SUBCLASS_CACHE[cache_key]

    for subclass in schema_base.__subclasses__():
        schema_model = getattr(subclass.Meta, "model", None)
        if schema_model == model and (getattr(subclass, "dump", False) is dump or getattr(subclass, "dump", None)):
            _SCHEMA_SUBCLASS_CACHE[cache_key] = subclass
            return subclass
    _SCHEMA_SUBCLASS_CACHE[cache_key] = None
    return None


def create_dynamic_schema(base_class: Callable, model_class: Callable) -> Callable:
    """Create a schema subclass for ``model_class`` at runtime.

    Why/How:
        When no explicit schema is provided, we generate a lightweight class
        deriving from ``base_class`` with a ``Meta.model`` binding so the rest
        of the pipeline can introspect fields and produce OpenAPI metadata.

    Args:
        base_class: The base schema class (typically ``AutoSchema``).
        model_class: The SQLAlchemy model to associate with.

    Returns:
        The dynamically created schema class.
    """

    class Meta:
        model = model_class

    cache_key = (base_class, model_class)
    if cache_key in _DYNAMIC_SCHEMA_CACHE:
        return _DYNAMIC_SCHEMA_CACHE[cache_key]

    dynamic_class = new_class(
        f"{model_class.__name__}Schema",
        (base_class,),
        exec_body=lambda ns: ns.update(Meta=Meta),
    )
    _DYNAMIC_SCHEMA_CACHE[cache_key] = dynamic_class
    return dynamic_class


def get_input_output_from_model_or_make(model: Callable, **kwargs) -> tuple[Callable, Callable]:
    """Return input/output schema instances for a model, creating them if needed.

    Why/How:
        Prefers user-supplied ``AutoSchema`` subclasses when present; otherwise
        falls back to dynamic classes. Flags like ``API_ADD_RELATIONS`` and
        ``API_DUMP_HYBRID_PROPERTIES`` influence which base is used.

    Args:
        model: The model to derive schemas for.

    Returns:
        A tuple of ``(input_schema, output_schema)`` instances.
    """
    from flarchitect.schemas.bases import AutoSchema

    disable_relations = not get_config_or_model_meta("API_ADD_RELATIONS", model=model, default=True)
    disable_hybrids = not get_config_or_model_meta("API_DUMP_HYBRID_PROPERTIES", model=model, default=True)

    if disable_relations or disable_hybrids:
        input_schema_class = create_dynamic_schema(AutoSchema, model)
        output_schema_class = create_dynamic_schema(AutoSchema, model)
    else:
        input_schema_class = get_schema_subclass(model, dump=False) or create_dynamic_schema(AutoSchema, model)
        output_schema_class = get_schema_subclass(model, dump=True) or create_dynamic_schema(AutoSchema, model)

    input_schema = input_schema_class(**kwargs)
    output_schema = output_schema_class(**kwargs)

    return input_schema, output_schema


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

        input_schema = input_schema is not callable(input_schema) and input_schema or input_schema()

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
        the model’s attributes and declared schema fields.

    Args:
        model: The SQLAlchemy model class.
        schema: The Marshmallow schema class.
        data_dict_list: List of input dictionaries.

    Returns:
        Filtered list of dictionaries.
    """
    model_keys, model_properties = _extract_model_attributes(model)
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
