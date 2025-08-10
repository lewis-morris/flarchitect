from collections.abc import Callable
from types import new_class
from typing import Any

from flask import Response, request
from marshmallow import Schema, ValidationError
from sqlalchemy.orm import DeclarativeBase

from flarchitect.database.utils import _extract_model_attributes
from flarchitect.utils.config_helpers import get_config_or_model_meta, is_xml


def get_schema_subclass(model: Callable, dump: bool | None = False) -> Callable | None:
    """Search for the appropriate AutoSchema subclass that matches the model and dump parameters.

    Args:
        model (Callable): The model to search for.
        dump (Optional[bool]): Whether to search for a dump or load schema.

    Returns:
        Optional[Callable]: The matching subclass of AutoSchema, if found.
    """
    from flarchitect.schemas.bases import AutoSchema

    schema_base = get_config_or_model_meta(
        "API_BASE_SCHEMA", model=model, default=AutoSchema
    )

    for subclass in schema_base.__subclasses__():
        schema_model = getattr(subclass.Meta, "model", None)
        if schema_model == model and (
            getattr(subclass, "dump", False) is dump or getattr(subclass, "dump", None)
        ):
            return subclass
    return None


def create_dynamic_schema(base_class: Callable, model_class: Callable) -> Callable:
    """Create a dynamic schema class that inherits from the base_class and associates with the model_class.

    Args:
        base_class (Callable): The base class to inherit from.
        model_class (Callable): The model class to associate with.

    Returns:
        Callable: The dynamically created schema class.
    """

    class Meta:
        model = model_class

    dynamic_class = new_class(
        f"{model_class.__name__}Schema",
        (base_class,),
        exec_body=lambda ns: ns.update(Meta=Meta),
    )
    return dynamic_class


def get_input_output_from_model_or_make(
    model: Callable, **kwargs
) -> tuple[Callable, Callable]:
    """Get or create input and output schema instances for the model.

    Args:
        model (Callable): The model to get the schemas from.

    Returns:
        Tuple[Callable, Callable]: The input and output schema instances.
    """
    from flarchitect.schemas.bases import AutoSchema

    input_schema_class = get_schema_subclass(
        model, dump=False
    ) or create_dynamic_schema(AutoSchema, model)
    output_schema_class = get_schema_subclass(
        model, dump=True
    ) or create_dynamic_schema(AutoSchema, model)

    input_schema = input_schema_class(**kwargs)
    output_schema = output_schema_class(**kwargs)

    return input_schema, output_schema


def deserialize_data(
    input_schema: type[Schema], response: Response
) -> dict[str, Any] | tuple[dict[str, Any], int]:
    """
    Utility function to deserialize data using a given Marshmallow schema.

    Args:
        input_schema (Type[Schema]): The Marshmallow schema to be used for deserialization.
        response (Response): The response object containing data to be deserialized.

    Returns:
        Union[Dict[str, Any], Tuple[Dict[str, Any], int]]: The deserialized data if successful, or a tuple containing
        errors and a status code if there's an error.
    """
    try:
        data = request.data.decode() if is_xml() else response.json

        hook = get_config_or_model_meta("API_GLOBAL_PRE_DESERIALIZE_HOOK", default=None)
        if hook:
            data = hook(data)

        input_schema = (
            input_schema is not callable(input_schema)
            and input_schema
            or input_schema()
        )

        if hasattr(input_schema, "fields"):
            fields = [
                v.attribute or k
                for k, v in input_schema.fields.items()
                if not v.dump_only
            ]
        else:
            fields = [
                v.attribute or k
                for k, v in input_schema._declared_fields.items()
                if not v.dump_only
            ]

        data = {
            k: v for k, v in data.get("deserialized_data", data).items() if k in fields
        }
        if request.method == "PATCH":
            from flarchitect.specs.utils import _prepare_patch_schema

            input_schema = _prepare_patch_schema(input_schema)

        try:
            deserialized_data = input_schema().load(data=data)
        except TypeError:
            deserialized_data = input_schema.load(data=data)

        return deserialized_data
    except ValidationError as err:
        return err.messages, 400


def filter_keys(
    model: type[DeclarativeBase], schema: type[Schema], data_dict_list: list[dict]
) -> list[dict]:
    """
    Filters keys from the data dictionary based on model attributes and schema fields.

    Args:
        model (Type[DeclarativeBase]): The SQLAlchemy model class.
        schema (Type[Schema]): The Marshmallow schema class.
        data_dict_list (List[Dict]): List of data dictionaries to be filtered.

    Returns:
        List[Dict]: The filtered list of data dictionaries.
    """
    model_keys, model_properties = _extract_model_attributes(model)
    schema_fields = set(schema._declared_fields.keys())
    all_model_keys = model_keys.union(model_properties)

    return [
        {
            key: value
            for key, value in data_dict.items()
            if key in all_model_keys or key in schema_fields
        }
        for data_dict in data_dict_list
    ]


def dump_schema_if_exists(
    schema: Schema, data: dict | DeclarativeBase, is_list: bool = False
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    Serialize the data using the schema if the data exists.

    Args:
        schema (Schema): The schema to use for serialization.
        data (Union[dict, DeclarativeBase]): The data to serialize.
        is_list (bool): Whether the data is a list.

    Returns:
        Union[Dict[str, Any], List[Dict[str, Any]]]: The serialized data.
    """
    return schema.dump(data, many=is_list) if data else ([] if is_list else None)


def list_schema_fields(schema: Schema) -> list[str]:
    """
    Returns the list of fields in a Marshmallow schema.

    Args:
        schema (Schema): The schema to extract fields from.

    Returns:
        List[str]: List of field names.
    """
    return list(schema.fields.keys())
