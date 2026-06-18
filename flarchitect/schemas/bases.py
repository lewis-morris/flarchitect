import datetime
import uuid
from collections.abc import Callable
from contextlib import suppress
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from types import new_class
from typing import Any, get_args, get_origin, get_type_hints

import sqlalchemy_utils
from flask import request
from marshmallow import Schema, ValidationError, fields, post_dump, pre_dump
from marshmallow.validate import Length, Range
from sqlalchemy import (
    TIMESTAMP,
    UUID,
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    Integer,
    Interval,
    LargeBinary,
    Numeric,
    SmallInteger,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import ColumnProperty, RelationshipProperty, class_mapper
from sqlalchemy.orm import exc as orm_exc
from sqlalchemy.types import JSON as SQLAlchemyJSON
from sqlalchemy.types import TypeDecorator
from sqlalchemy_utils.types.email import EmailType

from flarchitect.logging import logger
from flarchitect.schemas.validators import validate_by_type
from flarchitect.specs.utils import endpoint_namer, get_openapi_meta_data
from flarchitect.utils.config_helpers import get_config_or_model_meta
from flarchitect.utils.core_utils import convert_case


class EnumField(fields.Field):
    """Custom field to handle Enum serialisation and deserialisation by key."""

    def __init__(self, enum, by_value=False, **kwargs):
        """Initialise the field.

        Args:
            enum: The Enum class to use.
            by_value: If True, serialise/deserialise using Enum values instead of keys.
            **kwargs: Additional keyword arguments.
        """
        self.enum = enum
        self.by_value = by_value
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        if not isinstance(value, self.enum):
            raise ValidationError(f"Expected type {self.enum}, got {type(value)}.")
        return value.value if self.by_value else value.name

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        try:
            if self.by_value:
                return self.enum(value)
            return self.enum[value]
        except (KeyError, ValueError) as e:
            valid = [e.name if not self.by_value else e.value for e in self.enum]
            raise ValidationError(f"Invalid enum value. Expected one of: {valid}.") from e


class NumericNumber(fields.Decimal):
    """Serialise ``Numeric`` values as JSON-native numbers."""

    def __init__(self, *args, **kwargs) -> None:
        kwargs.setdefault("as_string", False)
        kwargs.setdefault("allow_nan", False)
        super().__init__(*args, **kwargs)

    def _serialize(self, value, attr, obj, **kwargs):  # type: ignore[override]
        serialised = super()._serialize(value, attr, obj, **kwargs)
        if serialised is None:
            return None
        if isinstance(serialised, Decimal):
            return float(serialised)
        return serialised


# Mapping between SQLAlchemy types and Marshmallow fields
type_mapping = {
    Integer: fields.Int,
    SmallInteger: fields.Int,  # Added SmallInteger
    String: fields.Str,
    Text: fields.Str,
    Boolean: fields.Bool,
    Float: fields.Float,
    Date: fields.Date,
    DateTime: fields.DateTime,
    Time: fields.Time,
    TIMESTAMP: fields.DateTime,  # Added TIMESTAMP
    JSON: fields.Raw,
    JSONB: fields.Raw,
    SQLAlchemyJSON: fields.Raw,
    Numeric: NumericNumber,
    BigInteger: fields.Int,
    LargeBinary: fields.Str,  # Consider using fields.Raw for binary data
    Enum: EnumField,  # Consider fields.Enum for stricter validation
    EmailType: fields.Email,  # Consider fields.Enum for stricter validation
    Interval: fields.TimeDelta,
    UUID: fields.UUID,  # Added UUID
    str: fields.Str,
    int: fields.Int,
    bool: fields.Bool,
    float: fields.Float,
    dict: fields.Dict,
    list: fields.List,
    sqlalchemy_utils.types.encrypted.encrypted_type.StringEncryptedType: fields.Str,  # Added StringEncryptedType
}


def register_type_mapping(sqlalchemy_type: Any, marshmallow_field: type[fields.Field]) -> None:
    """Register or override a SQLAlchemy → Marshmallow field mapping.

    Args:
        sqlalchemy_type: SQLAlchemy type (class or instance) to recognise.
        marshmallow_field: Marshmallow ``Field`` subclass that handles values of
            ``sqlalchemy_type``.
    """

    type_mapping[sqlalchemy_type] = marshmallow_field


_FIELD_CACHE_CONFIG_KEYS = (
    "API_ADD_RELATIONS",
    "API_ALLOW_JOIN",
    "API_DUMP_HYBRID_PROPERTIES",
    "API_FIELD_CASE",
    "API_IGNORE_UNDERSCORE_ATTRIBUTES",
    "API_SCHEMA_CASE",
    "API_SERIALIZATION_DEPTH",
    "API_SERIALIZATION_TYPE",
    "ALLOW_NESTED_WRITES",
)
_SchemaFieldCacheKey = tuple[type["AutoSchema"], bool, int, int, tuple[str, ...] | None, tuple[tuple[str, str], ...]]
_SCHEMA_FIELD_CACHE: dict[_SchemaFieldCacheKey, "_SchemaFieldCacheEntry"] = {}
_HYBRID_FIELD_CACHE: dict[tuple[type[Any], str], tuple[type[fields.Field], dict[str, Any]]] = {}
_AUTO_SCHEMA_REGISTRY: dict[tuple[type[Any], bool | None], list[type["AutoSchema"]]] = {}
_SCHEMA_SUBCLASS_CACHE: dict[tuple[type[Any], bool | None], Callable[..., Any] | None] = {}
_DYNAMIC_SCHEMA_CACHE: dict[tuple[type[Any], type[Any]], type[Any]] = {}
_JOIN_QUERY_KEYS = {"join", "join_models"}
_RESERVED_JOIN_QUERY_KEYS = {
    "join",
    "join_models",
    "join_type",
    "fields",
    "groupby",
    "orderby",
    "order_by",
    "page",
    "limit",
    "dump",
    "format",
    "include_deleted",
    "cascade_delete",
}
_DIRECT_FORMAT_VALIDATORS = {
    "ipv4": "ipv4",
    "ipv6": "ipv6",
    "mac": "mac",
    "hostname": "hostname",
    "slug": "slug",
    "card": "card",
    "country_code": "country_code",
    "iban": "iban",
    "cron": "cron",
    "base64": "base64",
    "sha224": "sha224",
    "sha384": "sha384",
    "currency": "currency",
}
_URL_FORMATS = {"url", "uri", "url_path"}
_PHONE_FORMATS = {"phone", "phone_number"}
_POSTAL_FORMATS = {"postal_code", "zip", "zipcode"}
_HYBRID_PRIMITIVE_TYPES: dict[str, Any] = {
    "int": int,
    "integer": int,
    "float": float,
    "bool": bool,
    "boolean": bool,
    "string": str,
    "str": str,
    "decimal": Decimal,
}


@dataclass(slots=True)
class _SchemaFieldCacheEntry:
    prototypes: dict[str, fields.Field]
    declared_map: dict[str, str]
    field_map: dict[str, str]
    load_map: dict[str, str]
    dump_map: dict[str, str]

    @classmethod
    def capture(cls, schema: "AutoSchema") -> "_SchemaFieldCacheEntry":
        token_map: dict[int, str] = {}
        prototypes: dict[str, fields.Field] = {}

        def _token_for(field: fields.Field) -> str:
            field_id = id(field)
            token = token_map.get(field_id)
            if token is None:
                token = f"f{len(token_map)}"
                token_map[field_id] = token
                prototypes[token] = _clone_field(field)
            return token

        return cls(
            prototypes=prototypes,
            declared_map={name: _token_for(field) for name, field in schema.declared_fields.items()},
            field_map={name: _token_for(field) for name, field in schema.fields.items()},
            load_map={name: _token_for(field) for name, field in schema.load_fields.items()},
            dump_map={name: _token_for(field) for name, field in schema.dump_fields.items()},
        )

    def instantiate(self, schema: "AutoSchema") -> None:
        instantiated = {token: _clone_field(proto) for token, proto in self.prototypes.items()}
        schema.declared_fields = {name: instantiated[token] for name, token in self.declared_map.items()}
        schema.fields = {name: instantiated[token] for name, token in self.field_map.items()}
        schema.load_fields = {name: instantiated[token] for name, token in self.load_map.items()}
        schema.dump_fields = {name: instantiated[token] for name, token in self.dump_map.items()}


def _clone_field(field: fields.Field) -> fields.Field:
    cloned = deepcopy(field)
    if hasattr(cloned, "parent"):
        cloned.parent = None
    if hasattr(cloned, "root"):
        cloned.root = None
    return cloned


def _register_auto_schema_subclass(cls: type["AutoSchema"]) -> None:
    meta = getattr(cls, "Meta", None)
    model = getattr(meta, "model", None)
    if model is None:
        return

    dump_value = getattr(cls, "dump", None)
    if dump_value is True:
        keys = [(model, True)]
    elif dump_value is None:
        keys = [(model, None)]
    else:
        keys = [(model, False)]

    for key in keys:
        registry = _AUTO_SCHEMA_REGISTRY.setdefault(key, [])
        if cls not in registry:
            registry.append(cls)


def lookup_auto_schema_subclass(model: type[Any], dump: bool | None, schema_base: type["AutoSchema"]) -> type["AutoSchema"] | None:
    if model is None:
        return None

    if dump is True:
        search_keys = [(model, True)]
    elif dump is False:
        search_keys = [(model, False)]
    else:
        search_keys = [(model, None), (model, False), (model, True)]

    for key in search_keys:
        for candidate in _AUTO_SCHEMA_REGISTRY.get(key, []):
            if issubclass(candidate, schema_base):
                return candidate
    return None


def get_schema_subclass(model: Callable[..., Any], dump: bool | None = False) -> Callable[..., Any] | None:
    """Locate an ``AutoSchema`` subclass for a model and usage direction."""

    if model is None:
        return None

    schema_base = get_config_or_model_meta("API_BASE_SCHEMA", model=model, default=AutoSchema) or AutoSchema

    cache_key = (model, dump)
    if cache_key in _SCHEMA_SUBCLASS_CACHE:
        return _SCHEMA_SUBCLASS_CACHE[cache_key]

    subclass = lookup_auto_schema_subclass(model, dump, schema_base)
    _SCHEMA_SUBCLASS_CACHE[cache_key] = subclass
    return subclass


def create_dynamic_schema(base_class: Callable[..., Any], model_class: Callable[..., Any]) -> Callable[..., Any]:
    """Create and cache a schema subclass for ``model_class`` at runtime."""

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


def get_input_output_from_model_or_make(model: Callable[..., Any], **kwargs) -> tuple[Callable[..., Any], Callable[..., Any]]:
    """Return input/output schema instances for a model, creating them if needed."""

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


def _normalise_join_token(value: object) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _request_join_tokens() -> set[str]:
    """Collect explicit relationship join tokens from the active request."""

    try:
        tokens: set[str] = set()
        for key in _JOIN_QUERY_KEYS:
            for value in request.args.getlist(key):
                tokens.update(token for raw in str(value).split(",") if (token := _normalise_join_token(raw)))

        for key in request.args:
            if key not in _RESERVED_JOIN_QUERY_KEYS and "__" not in key and "." not in key and (token := _normalise_join_token(key)):
                tokens.add(token)
        return tokens
    except Exception:
        return set()


def _relationship_join_candidates(original_attribute: str, related_model: type[Any]) -> set[str]:
    endpoint_case = get_config_or_model_meta("API_ENDPOINT_CASE", default="kebab") or "kebab"
    endpoint_name = get_config_or_model_meta("API_ENDPOINT_NAMER", related_model, default=endpoint_namer)(related_model)
    return {
        _normalise_join_token(endpoint_name),
        _normalise_join_token(convert_case(original_attribute, endpoint_case)),
        _normalise_join_token(original_attribute),
    }


def _safe_column_python_type(column: Column) -> type | None:
    try:
        return column.type.python_type
    except Exception:
        return None


def _auto_validator_name(
    *,
    column_name: str,
    format_name: str | None,
    python_type: type | None,
    column: Column,
) -> str | None:
    rules = (
        ((("email" in column_name and python_type is str) or format_name == "email"), "email"),
        ((("url" in column_name and python_type is str) or format_name in _URL_FORMATS), "url"),
        ((("date" in column_name or python_type is datetime.date or format_name == "date")), "date"),
        ((python_type is datetime.time or format_name == "time"), "time"),
        ((("datetime" in column_name or python_type is datetime.datetime or format_name == "datetime")), "datetime"),
        ((("boolean" in column_name or python_type is bool or format_name == "boolean")), "boolean"),
        ((("domain" in column_name and python_type is str) or format_name == "domain"), "domain"),
    )
    for matched, validator_name in rules:
        if matched:
            return validator_name
    if format_name in _DIRECT_FORMAT_VALIDATORS:
        return _DIRECT_FORMAT_VALIDATORS[format_name]
    if format_name == "uuid" or _safe_column_python_type(column) is uuid.UUID:
        return "uuid"
    if ("phone" in column_name and _safe_column_python_type(column) is str) or format_name in _PHONE_FORMATS:
        return "phone"
    if "postal" in column_name or "zip" in column_name or format_name in _POSTAL_FORMATS:
        return "postal_code"
    return None


def _model_class_for_schema_model(model: Any) -> type[Any] | None:
    if isinstance(model, type):
        return model
    if model is not None:
        return type(model)
    return None


def _normalise_hybrid_field_type(field_type: Any | None) -> Any | None:
    if isinstance(field_type, str):
        return _HYBRID_PRIMITIVE_TYPES.get(field_type.lower())

    origin = get_origin(field_type)
    if origin is None:
        return field_type

    args = [arg for arg in get_args(field_type) if arg is not type(None)]
    return args[0] if len(args) == 1 else origin


def _hybrid_return_type(descriptor: Any) -> Any | None:
    fget = getattr(descriptor, "fget", None)
    if fget is None:
        return None

    try:
        return get_type_hints(fget).get("return")
    except Exception:
        return getattr(fget, "__annotations__", {}).get("return")


def _schema_field_class_for_type(field_type: Any | None) -> type[fields.Field]:
    if isinstance(field_type, type) and issubclass(field_type, fields.Field):
        return field_type

    resolved = type_mapping.get(field_type, fields.Str) if field_type else fields.Str
    return resolved if isinstance(resolved, type) else fields.Str


class Base(Schema):  # Inheriting from marshmallow's Schema
    def __init__(self, *args, context=None, **kwargs):
        # 1️⃣  Stash the context *before* super().__init__
        #     (marshmallow 4 no longer accepts it)
        self.context: dict = context or {}
        super().__init__(*args, **kwargs)

    def get_attribute(self, obj, attr, default):
        """Safely resolve attributes during serialisation.

        Guards against SQLAlchemy ``DetachedInstanceError`` when objects are
        detached from their session at dump time. Controlled by
        ``API_SERIALIZATION_IGNORE_DETACHED`` (default True). When enabled,
        missing/unloaded attributes resolve to the provided ``default`` rather
        than raising.
        """
        ignore_detached = get_config_or_model_meta("API_SERIALIZATION_IGNORE_DETACHED", default=True)
        try:
            return super().get_attribute(obj, attr, default)
        except orm_exc.DetachedInstanceError:
            if ignore_detached:
                # Return a concrete null-ish value so the field serialises
                # explicitly rather than being omitted as "missing".
                return None
            raise

    @classmethod
    def get_model(cls):
        """Get the SQLAlchemy model associated with the schema."""
        meta = getattr(cls, "Meta", None)
        return getattr(meta, "model", None)


class DeleteSchema(Base):
    complete = fields.Boolean(required=True)


class AutoSchema(Base):
    class Meta:
        model = None
        add_hybrid_properties = True
        include_children = True

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        _register_auto_schema_subclass(cls)

    def __init__(self, *args, render_nested=True, **kwargs):
        """Initialise the ``AutoSchema`` instance.

        Why/How:
            Configures field generation against the bound model, sets case
            conversion preferences and prepares context for nested rendering.
        """
        self.render_nested = render_nested
        self.depth = kwargs.pop("depth", 0)
        only_fields = kwargs.pop("only", None)
        self._cache_only_key = self._normalise_only(only_fields)

        # Ensure context is set up properly
        super().__init__(*args, **kwargs)

        if "context" not in kwargs or kwargs["context"] is None:
            kwargs["context"] = {}

        kwargs["context"].setdefault("current_depth", self.depth)
        self.context = kwargs["context"]

        self.model = self.Meta.model

        if self.model:
            schema_case = get_config_or_model_meta("API_SCHEMA_CASE", model=self.model, default="camel")
            self.__name__ = convert_case(self.model.__name__, schema_case)
            self.generate_fields()

        if only_fields:
            self._apply_only(only_fields)

    @staticmethod
    def _normalise_only(value: Any) -> tuple[str, ...] | None:
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return tuple(value)
        if isinstance(value, set):
            return tuple(sorted(value))
        return (value,)

    def _field_cache_config_fingerprint(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (key, repr(get_config_or_model_meta(key, self.model, default=None)))
            for key in _FIELD_CACHE_CONFIG_KEYS
        )

    def _build_field_cache_key(self) -> _SchemaFieldCacheKey:
        return (
            self.__class__,
            bool(self.render_nested),
            int(self.depth or 0),
            int(self.context.get("current_depth", 0) or 0),
            self._cache_only_key,
            self._field_cache_config_fingerprint(),
        )

    def _can_use_field_cache(self) -> bool:
        """Field generation is request-sensitive when dump/join args are present."""

        try:
            if request.args:
                return False
        except RuntimeError:
            pass

        raw_dump = get_config_or_model_meta("API_SERIALIZATION_TYPE", self.model, default="url")
        return str(raw_dump or "url").strip().lower() != "dynamic"

    @pre_dump
    def pre_dump(self, data, **kwargs):
        # print("Pre-dump data:", data)
        return data  # Ensure the data is returned unchanged

    @post_dump
    def post_dump(self, data: dict, **kwargs) -> dict:
        """Apply a post-dump callback if configured."""
        post_dump_function = get_config_or_model_meta(
            "API_DUMP_CALLBACK",
            model=self.get_model(),
            method=request.method,
            default=None,
        )
        return post_dump_function(data, **kwargs) if post_dump_function else data

    def _apply_only(self, only_fields: list):
        """Filter fields to include only those specified."""
        self.fields = {key: self.fields[key] for key in only_fields}
        # todo Add a check to see if ok to dump or not

        self.dump_fields = {key: self.dump_fields[key] for key in only_fields}
        self.load_fields = {key: self.load_fields[key] for key in only_fields}

    def _generate_field_for_descriptor(self, original_attribute: str, mapper_property: Any) -> None:
        if self._should_skip_attribute(original_attribute):
            return

        attribute = self._convert_case(original_attribute)
        prop = getattr(mapper_property, "property", None)

        if isinstance(prop, RelationshipProperty):
            self._handle_relationship(attribute, original_attribute, mapper_property)
        elif isinstance(prop, ColumnProperty):
            self._handle_column(attribute, original_attribute, mapper_property)
        elif isinstance(mapper_property, hybrid_property) and get_config_or_model_meta("API_DUMP_HYBRID_PROPERTIES", model=self.model, default=True):
            self._handle_hybrid_property(attribute, original_attribute, mapper_property)

    def generate_fields(self):
        """Automatically add fields for each column and relationship in the SQLAlchemy model."""
        if not self.model:
            logger.warning("self.Meta.model is None. Skipping field generation.")
            return

        use_field_cache = self._can_use_field_cache()
        cache_key = self._build_field_cache_key()
        if use_field_cache:
            cached_entry = _SCHEMA_FIELD_CACHE.get(cache_key)
            if cached_entry is not None:
                cached_entry.instantiate(self)
                _rebind_cached_fields(self)
                return

        mapper = class_mapper(self.model)
        for attribute, mapper_property in mapper.all_orm_descriptors.items():
            self._generate_field_for_descriptor(attribute, mapper_property)

        if use_field_cache:
            _SCHEMA_FIELD_CACHE[cache_key] = _SchemaFieldCacheEntry.capture(self)

    def _convert_case(self, attribute: str) -> str:
        """Convert the attribute name to the appropriate case.

        Preserves a leading underscore when ``API_IGNORE_UNDERSCORE_ATTRIBUTES``
        is ``False`` so that hidden fields remain visibly prefixed in outputs.
        """
        field_case = get_config_or_model_meta("API_FIELD_CASE", model=self.model, default="snake")
        has_leading_underscore = attribute.startswith("_")
        # Convert without the leading underscore to get correct casing
        base = attribute.lstrip("_") if has_leading_underscore else attribute
        converted = convert_case(base, field_case)
        if has_leading_underscore and not get_config_or_model_meta("API_IGNORE_UNDERSCORE_ATTRIBUTES", model=self.model, default=True):
            return f"_{converted}"
        return converted

    def _should_skip_attribute(self, attribute: str) -> bool:
        """Determine if the attribute should be skipped.

        Uses the original attribute name to detect a leading underscore.
        """
        return attribute.startswith("_") and get_config_or_model_meta("API_IGNORE_UNDERSCORE_ATTRIBUTES", model=self.model, default=True)

    def _handle_relationship(
        self,
        attribute: str,
        original_attribute: str,
        mapper_property: RelationshipProperty,
    ):
        """Handle adding a relationship field to the schema."""
        if not self.render_nested:
            return

        add_relations = get_config_or_model_meta("API_ADD_RELATIONS", model=self.model, default=True)
        allow_join = get_config_or_model_meta("API_ALLOW_JOIN", model=self.model, default=False)

        # Respect per-request opt-out for dumping relationships entirely
        try:
            if request.args.get("dump_relationships") in ["false", "False", "0"]:
                return
        except RuntimeError:
            # this happens when the model is outside the flask request and is expected when the schema is first
            # initialised
            pass

        # If relations are globally disabled, still allow explicit inclusion
        # when joins are both allowed and requested for this relationship.
        if not add_relations:
            if not allow_join:
                return
            related_model = mapper_property.property.mapper.class_
            if _request_join_tokens().isdisjoint(_relationship_join_candidates(original_attribute, related_model)):
                return

        # Either relations are enabled or an explicit join requested this one
        self.add_relationship_field(attribute, original_attribute, mapper_property)

    def _handle_column(self, attribute: str, original_attribute: str, mapper_property: ColumnProperty):
        """Handle adding a column field to the schema."""
        column_type = mapper_property.property.columns[0].type
        self.add_column_field(attribute, original_attribute, column_type)

    def _handle_hybrid_property(self, attribute: str, original_attribute: str, mapper_property: hybrid_property):
        """Handle adding a hybrid property field to the schema."""
        self.add_hybrid_property_field(
            attribute,
            original_attribute,
            mapper_property.__annotations__.get("return"),
        )

    def add_hybrid_property_field(self, attribute: str, original_attribute: str, field_type: Any | None):
        """Automatically add a field for a given hybrid property in the SQLAlchemy model."""
        if self._should_skip_attribute(attribute):
            return

        field_type = _normalise_hybrid_field_type(field_type)
        model_cls = _model_class_for_schema_model(self.model)
        cache_key = (model_cls, original_attribute) if model_cls is not None else None
        cached = _HYBRID_FIELD_CACHE.get(cache_key) if cache_key else None

        if cached is not None:
            schema_field_cls, cached_args = cached
            field_args = dict(cached_args)
        else:
            descriptor = getattr(model_cls, original_attribute, None) if model_cls is not None else None

            if field_type is None and descriptor is not None:
                field_type = _normalise_hybrid_field_type(_hybrid_return_type(descriptor))

            # Check if the attribute has a setter method (properties/hybrids expose ``fset``)
            has_setter = descriptor is not None and getattr(descriptor, "fset", None) is not None

            # If there's no setter, mark it as dump_only
            schema_field_cls = _schema_field_class_for_type(field_type)
            field_args = {"dump_only": not has_setter}

            if cache_key:
                _HYBRID_FIELD_CACHE[cache_key] = (schema_field_cls, dict(field_args))

        field = schema_field_cls(data_key=attribute, **dict(field_args))

        self.add_to_fields(original_attribute, field, load=False)

        self._update_field_metadata(original_attribute)

    def add_column_field(self, attribute: str, original_attribute: str, column_type: Any) -> None:
        """Add a schema field for a SQLAlchemy column.

        Args:
            attribute (str): Name of the field exposed by the schema.
            original_attribute (str): Name of the attribute on the SQLAlchemy model.
            column_type (Any): SQLAlchemy column type instance being converted.

        Returns:
            None: The field is added directly to ``self.fields`` and related mappings.

        Assumptions:
            ``column_type`` is either an ``Enum`` or present in ``type_mapping``.

        Side Effects:
            Mutates ``self`` by inserting the generated field and updating its
            metadata via :meth:`_update_field_metadata`.
        """

        # Check if the attribute should be skipped
        if self._should_skip_attribute(attribute):
            return

        # Handle Enum types separately
        if isinstance(column_type, Enum):
            enum_class = column_type.enum_class  # Extract the Enum class
            field_args = self._get_column_field_attrs(original_attribute, column_type)
            field = EnumField(
                enum=enum_class,  # Provide the enum class
                data_key=attribute,
                **field_args,
            )
        else:
            # Map the SQLAlchemy column type to a Marshmallow field type
            field_type, resolved_type = self._resolve_field_type(column_type)
            if not field_type:
                logger.error(1, f"No field mapping for column type: {type(column_type)}")
                return

            # Get additional attrs for the field based on the column's properties
            field_args = self._get_column_field_attrs(original_attribute, column_type, resolved_type)

            numeric_source = resolved_type or column_type

            if issubclass(field_type, NumericNumber) and self._is_instance_or_subclass(numeric_source, Numeric):
                scale = getattr(numeric_source, "scale", None)
                if scale is not None:
                    field_args.setdefault("places", scale)

            # Instantiate the field
            field = field_type(data_key=attribute, **field_args)

        # Add the field to the schema
        self.add_to_fields(original_attribute, field)

        # Update the OpenAPI metadata for the field
        self._update_field_metadata(original_attribute)

    def add_to_fields(self, attribute: str, field: fields.Field, load: bool = True, dump: bool = True) -> None:
        """Register a field on the schema.

        Args:
            attribute (str): Attribute name on the schema.
            field (fields.Field): Marshmallow field to register.
            load (bool, optional): Whether the field should be available for loading.
            dump (bool, optional): Whether the field should be available for dumping.

        Returns:
            None

        Side Effects:
            Updates ``declared_fields``, ``fields``, ``load_fields`` and
            ``dump_fields`` dictionaries on the schema.
        """
        self.declared_fields[attribute] = field

        self.fields[attribute] = field
        if load:
            self.load_fields[attribute] = field
        if dump:
            self.dump_fields[attribute] = field

    def _get_column_field_attrs(self, original_attribute: str, column_type: Any, effective_type: Any | None = None) -> dict[str, Any]:
        """Compute Marshmallow field arguments for a model column.

        Args:
            original_attribute (str): Name of the column on the SQLAlchemy model.
            column_type (Any): SQLAlchemy column type instance.

        Returns:
            dict[str, Any]: Keyword arguments to apply when instantiating the field.

        Assumptions:
            ``self.model`` exposes ``__table__`` and ``original_attribute`` exists on it.
        """
        column = self.model.__table__.columns.get(original_attribute)

        # Check if column is None
        if column is None:
            return {}

        field_args = {}

        # Check for non-nullable columns that are not primary keys and auto-increment
        if not column.nullable and not column.primary_key and column.autoincrement and column.default is None:
            field_args["required"] = True

        # Handle default values for the column
        # Don't need default if db handling it.
        # if column.default:
        #     field_args["default"] = (
        #         column.default.arg if not callable(column.default.arg) else None
        #     )

        field_args["validate"] = []
        # Check for column length constraints and add validation
        field_args = self._add_validation(column, field_args, effective_type)

        # NO UNIQUE FIELD ANY MORE??!?
        # Mark fields as unique or primary keys
        # if column.unique or column.primary_key:
        #     field_args["unique"] = True

        if column.nullable:
            field_args["allow_none"] = True

        if column.comment:
            field_args["description"] = column.comment

        return field_args

    def _resolve_field_type(self, column_type: Any) -> tuple[type[fields.Field] | None, Any | None]:
        """Resolve the Marshmallow field for a SQLAlchemy column type.

        Handles ``TypeDecorator`` wrappers by traversing their ``impl`` chain
        (and any dialect-specific implementations) until a known mapping is
        located.
        """

        for candidate in self._iter_column_type_candidates(column_type):
            field_type = self._lookup_field_mapping(candidate)
            if field_type:
                resolved = candidate
                return field_type, resolved
        return None, None

    def _iter_column_type_candidates(self, column_type: Any):
        """Yield potential SQLAlchemy types for mapping, unwrapping decorators."""

        queue: list[Any] = [column_type]
        seen_ids: set[int] = set()
        seen_types: set[type] = set()

        while queue:
            current = queue.pop(0)

            if isinstance(current, type):
                if current in seen_types:
                    continue
                seen_types.add(current)
            else:
                marker = id(current)
                if marker in seen_ids:
                    continue
                seen_ids.add(marker)

            yield current

            if isinstance(current, TypeDecorator):
                impl = getattr(current, "impl", None)
                if impl is not None:
                    queue.append(impl)
                    if isinstance(impl, type):
                        with suppress(Exception):
                            queue.append(impl())

                loaded_impl = self._load_dialect_impl(current)
                if loaded_impl is not None:
                    queue.append(loaded_impl)

    def _lookup_field_mapping(self, candidate: Any) -> type[fields.Field] | None:
        if candidate in type_mapping:
            return type_mapping[candidate]

        keys: list[Any] = []
        if isinstance(candidate, type):
            keys.append(candidate)
        else:
            keys.append(type(candidate))

        for key in keys:
            field_type = type_mapping.get(key)
            if field_type:
                return field_type
        return None

    def _load_dialect_impl(self, decorator: TypeDecorator) -> Any | None:
        loader = getattr(decorator, "load_dialect_impl", None)
        if not callable(loader):
            return None

        try:
            from sqlalchemy.dialects import registry

            default_dialect_cls = registry.load("default")
            dialect = default_dialect_cls()
        except Exception:
            return None

        try:
            return loader(dialect)
        except Exception:
            return None

    def _is_instance_or_subclass(self, candidate: Any, expected: Any) -> bool:
        try:
            if isinstance(candidate, type):
                return issubclass(candidate, expected)
            return isinstance(candidate, expected)
        except TypeError:
            return False

    def _safe_python_type(self, candidate: Any) -> type | None:
        """Best-effort resolution of ``python_type`` for SQLAlchemy types."""

        sources: list[Any] = []
        if not isinstance(candidate, type):
            sources.append(candidate)
        if isinstance(candidate, type):
            try:
                instance = candidate()
            except Exception:
                instance = None
            if instance is not None:
                sources.append(instance)

        for source in sources:
            if not hasattr(source, "python_type"):
                continue
            python_type = self._python_type_or_none(source)
            if python_type is None:
                return None
            return python_type

        return None

    @staticmethod
    def _python_type_or_none(source: Any) -> type | None:
        """Return SQLAlchemy ``python_type`` when available and implemented."""

        try:
            return source.python_type
        except NotImplementedError:
            return None

    def _add_validation(self, column: Column, field_args: dict, effective_type: Any | None = None):
        # custom validation by user
        if column.info.get("validate"):
            validator = validate_by_type(column.info.get("validate"))
            if not validator:
                raise ValueError(f"Invalid validator type: model {self.model.__name__}.{column.name} - {column.info.get('validate')}")
            field_args["validate"].append(validator)
            return field_args

        # Add validation to the field based on the column type in sql
        length_source = effective_type or column.type
        length_value = getattr(length_source, "length", getattr(column.type, "length", None))
        if length_value is not None and not self._is_instance_or_subclass(length_source, Enum):
            field_args["validate"].append(Length(max=length_value))

        numeric_source = effective_type or column.type
        if self._is_instance_or_subclass(numeric_source, (Float, Numeric)):
            field_args["validate"].append(Range(min=float("-inf"), max=float("inf")))

        integer_source = effective_type or column.type
        if self._is_instance_or_subclass(integer_source, Integer):
            field_args["validate"].append(Range(min=-2147483648, max=2147483647))

        if get_config_or_model_meta("API_AUTO_VALIDATE", model=self.model, default=True):
            # todo add more validation and test
            column_name = column.name
            format_name = column.info.get("format")
            type_source = effective_type or column.type
            python_type = self._safe_python_type(type_source)
            if python_type is None:
                python_type = self._safe_python_type(column.type)
            try:
                validator_name = _auto_validator_name(
                    column_name=column_name,
                    format_name=format_name,
                    python_type=python_type,
                    column=column,
                )
                if validator_name:
                    field_args["validate"].append(validate_by_type(validator_name))
            except Exception:
                pass

        return field_args

    def get_url(self, obj: Any, attribute: str, other_schema: Schema) -> str | list[str] | None:
        """Resolve a URL for a related object.

        Args:
            obj (Any): Parent object from which to read the relationship.
            attribute (str): Relationship attribute name on ``obj``.
            other_schema (Schema): Related schema class; currently unused but
                reserved for future customization.

        Returns:
            str | list[str] | None: URL or list of URLs returned from the related
            object's ``to_url`` method, or ``None`` if the relationship is empty.

        Assumptions:
            Related objects implement a ``to_url`` method.
        """
        try:
            related = getattr(obj, attribute)
        except orm_exc.DetachedInstanceError:
            if get_config_or_model_meta("API_SERIALIZATION_IGNORE_DETACHED", default=True):
                return None
            raise

        if isinstance(related, list):
            try:
                return [item.to_url() for item in related]
            except orm_exc.DetachedInstanceError:
                if get_config_or_model_meta("API_SERIALIZATION_IGNORE_DETACHED", default=True):
                    return []
                raise
        elif related:
            try:
                return related.to_url()
            except orm_exc.DetachedInstanceError:
                if get_config_or_model_meta("API_SERIALIZATION_IGNORE_DETACHED", default=True):
                    return None
                raise
        else:
            return None

    def get_many_url(self, obj: Any, attribute: str, other_schema: Schema) -> str | list[str]:
        """Resolve URLs for collection relationships.

        Args:
            obj (Any): Parent object from which to read the relationship.
            attribute (str): Relationship attribute name on ``obj``.
            other_schema (Schema): Schema class describing the related model.

        Returns:
            str | list[str]: Result of calling the generated ``*_to_url`` method
            on ``obj`` for the related model.

        Assumptions:
            ``obj`` exposes a ``<child>_to_url`` method for the related model as
            determined by the configured endpoint namer.
        """

        child_end = get_config_or_model_meta("API_ENDPOINT_NAMER", other_schema.Meta.model, default=endpoint_namer)(other_schema.Meta.model)
        try:
            return getattr(obj, child_end.replace("-", "_") + "_to_url")()
        except orm_exc.DetachedInstanceError:
            if get_config_or_model_meta("API_SERIALIZATION_IGNORE_DETACHED", default=True):
                return []
            raise

    def _relationship_dump_type(self) -> str:
        try:
            dump_override = request.args.get("dump")
        except RuntimeError:
            dump_override = None
        dump_override = (dump_override or "").strip().lower()
        raw_dump = get_config_or_model_meta("API_SERIALIZATION_TYPE", self.model, default="url")
        configured_dump = "json" if raw_dump is False else str(raw_dump or "url").strip().lower()
        return dump_override if dump_override in {"url", "json", "dynamic", "hybrid"} else configured_dump

    def _relationship_serialization_depth(self) -> int | None:
        raw_depth = get_config_or_model_meta("API_SERIALIZATION_DEPTH", model=self.model, default=None)
        if raw_depth in (None, "") or raw_depth is False:
            return None
        try:
            depth = int(raw_depth)
        except (TypeError, ValueError):
            return None
        return depth if depth >= 0 else None

    def _add_relationship_url_field(
        self,
        attribute: str,
        original_attribute: str,
        input_schema: Schema,
        relationship_prop: Any,
        related_model: type[Any],
        field_args: dict[str, Any],
    ) -> str:
        if relationship_prop.uselist:
            field = fields.Function(lambda obj: self.get_many_url(obj, original_attribute, input_schema), **field_args)
            url_kind = "many"
        else:
            field = fields.Function(lambda obj: self.get_url(obj, original_attribute, input_schema), **field_args)
            url_kind = "single"
        field.metadata.setdefault("_fa_relationship", {}).update(
            {
                "kind": "url",
                "url_kind": url_kind,
                "attribute": original_attribute,
                "related_model": related_model,
            },
        )
        self.add_to_fields(attribute, field, load=False)
        return attribute

    def _add_relationship_nested_field(
        self,
        original_attribute: str,
        output_schema: Schema,
        relationship_prop: Any,
        related_model: type[Any],
        field_args: dict[str, Any],
    ) -> str:
        field = fields.List(fields.Nested(output_schema), **field_args) if relationship_prop.uselist else fields.Nested(output_schema, **field_args)
        field.metadata.setdefault("_fa_relationship", {}).update(
            {
                "kind": "nested",
                "role": "output",
                "many": bool(relationship_prop.uselist),
                "attribute": original_attribute,
                "related_model": related_model,
            },
        )
        self.add_to_fields(original_attribute, field, load=False)
        return original_attribute

    def _dynamic_relationship_requested(self, original_attribute: str, related_model: type[Any]) -> bool:
        tokens = _request_join_tokens()
        return bool(tokens) and not tokens.isdisjoint(_relationship_join_candidates(original_attribute, related_model))

    def _add_relationship_load_field(
        self,
        field_name: str,
        input_schema: Schema,
        relationship_prop: Any,
        original_attribute: str,
        related_model: type[Any],
    ) -> None:
        load_field = fields.List(fields.Nested(input_schema), load_only=True) if relationship_prop.uselist else fields.Nested(input_schema, load_only=True)
        load_field.metadata.setdefault("_fa_relationship", {}).update(
            {
                "kind": "nested",
                "role": "input",
                "many": bool(relationship_prop.uselist),
                "attribute": original_attribute,
                "related_model": related_model,
            },
        )
        self.add_to_fields(field_name, load_field, dump=False)

    def _add_relationship_output_field(
        self,
        *,
        dump_type: str,
        original_attribute: str,
        related_model: type[Any],
        relationship_prop: Any,
        depth_exceeded: bool,
        add_url_field: Callable[[], str],
        add_nested_field: Callable[[], str],
    ) -> str | None:
        if dump_type == "url":
            return add_url_field()
        if dump_type == "json":
            return add_url_field() if depth_exceeded else add_nested_field()
        if dump_type == "dynamic":
            return add_nested_field() if self._dynamic_relationship_requested(original_attribute, related_model) else None
        if dump_type == "hybrid":
            return add_url_field() if relationship_prop.uselist or depth_exceeded else add_nested_field()
        return add_nested_field()

    def _schema_field_for_metadata(self, field_key: str) -> fields.Field | None:
        return (
            self.fields.get(field_key)
            or self.dump_fields.get(field_key)
            or self.load_fields.get(field_key)
        )

    def _model_attribute_info(self, attribute: str) -> dict[str, Any] | None:
        try:
            mapper_property = class_mapper(self.model).get_property(attribute)
        except Exception:
            return None

        columns = getattr(mapper_property, "columns", None)
        if not columns:
            return None

        try:
            column = columns[0]
        except (IndexError, TypeError):
            return None

        return getattr(column, "info", None)

    def _merge_column_info_metadata(self, field_meta: dict[str, Any], info: dict[str, Any] | None) -> None:
        if not info:
            return
        for key in ("description", "example", "format"):
            if value := info.get(key):
                field_meta.setdefault(key, value)

    def add_relationship_field(
        self,
        attribute: str,
        original_attribute: str,
        relationship_property: RelationshipProperty,
    ) -> None:
        """Add serialisation fields for a SQLAlchemy relationship."""

        allow_nested_writes = get_config_or_model_meta("ALLOW_NESTED_WRITES", model=self.model, default=False)
        max_depth = 2 if allow_nested_writes else 1
        current_depth = self.context.get("current_depth", 0)

        if current_depth >= max_depth:
            return

        input_schema, output_schema = get_input_output_from_model_or_make(
            relationship_property.mapper.class_,
            context={"current_depth": current_depth + 1},
        )

        relationship_prop = relationship_property.property
        related_model = relationship_property.mapper.class_
        field_args = {"dump_only": not relationship_prop.viewonly}
        dump_type = self._relationship_dump_type()
        serialization_depth = self._relationship_serialization_depth()

        def add_url_field() -> str:
            return self._add_relationship_url_field(
                attribute,
                original_attribute,
                input_schema,
                relationship_prop,
                related_model,
                field_args,
            )

        def add_nested_field() -> str:
            return self._add_relationship_nested_field(
                original_attribute,
                output_schema,
                relationship_prop,
                related_model,
                field_args,
            )

        field_name = self._add_relationship_output_field(
            dump_type=dump_type,
            original_attribute=original_attribute,
            related_model=related_model,
            relationship_prop=relationship_prop,
            depth_exceeded=serialization_depth is not None and current_depth >= serialization_depth,
            add_url_field=add_url_field,
            add_nested_field=add_nested_field,
        )
        if field_name is None:
            return

        self._update_field_metadata(original_attribute, field_name)

        if allow_nested_writes and not relationship_prop.viewonly:
            self._add_relationship_load_field(
                field_name,
                input_schema,
                relationship_prop,
                original_attribute,
                related_model,
            )

    def _update_field_metadata(self, attribute: str, schema_attribute: str | None = None) -> None:
        """Populate OpenAPI metadata for a field.

        Args:
            attribute (str): Field name whose metadata should be updated.
            schema_attribute: Optional schema attribute key when it differs from
                the model attribute (for example, case-converted names).

        Returns:
            None

        Side Effects:
            Mutates the field's ``metadata`` dictionary in-place.
        """
        field_key = schema_attribute or attribute
        field_obj = self._schema_field_for_metadata(field_key)
        if field_obj is None:
            return

        field_meta = field_obj.metadata  # Extract the existing metadata
        self._merge_column_info_metadata(field_meta, self._model_attribute_info(attribute))

        # Merge additional OpenAPI-specific metadata derived from the field
        openapi_meta_data = get_openapi_meta_data(field_obj)
        if openapi_meta_data:
            field_meta.update(openapi_meta_data)

    def dump(self, obj, *args, **kwargs):
        # print("Data before super().dump:", obj)
        return super().dump(obj, *args, **kwargs) if self.fields else self.__class__(context=self.context).dump(obj, *args, **kwargs)


def _rebind_cached_fields(schema: "AutoSchema") -> None:
    related_schema_cache: dict[tuple[type[Any], int, bool], tuple[Schema, Schema]] = {}
    seen: set[int] = set()

    def _schemas_for(model_cls: type[Any], *, render_nested: bool = False) -> tuple[Schema, Schema]:
        current_depth = schema.context.get("current_depth", 0)
        cache_key = (model_cls, current_depth, render_nested)
        cached = related_schema_cache.get(cache_key)
        if cached is None:
            cached = get_input_output_from_model_or_make(
                model_cls,
                context={"current_depth": current_depth + 1},
                render_nested=render_nested,
            )
            related_schema_cache[cache_key] = cached
        return cached

    for mapping_name in ("declared_fields", "fields", "load_fields", "dump_fields"):
        mapping = getattr(schema, mapping_name)
        for field_name, field_obj in mapping.items():
            marker = id(field_obj)
            if marker in seen:
                continue
            seen.add(marker)
            _rebind_cached_field(schema, field_name, field_obj, _schemas_for)


def _assign_nested_schema(nested_field: fields.Nested, bound_schema: Schema) -> None:
    """Bind a fresh schema instance into a cached Marshmallow Nested field."""

    # ``Nested.schema`` is a read-only property backed by ``_schema``.
    nested_field._schema = bound_schema  # type: ignore[attr-defined]
    nested_field.nested = bound_schema.__class__

    if hasattr(nested_field, "parent"):
        nested_field.parent = None
    if hasattr(nested_field, "root"):
        nested_field.root = None


def _rebind_url_field(
    schema: "AutoSchema",
    field_obj: fields.Field,
    relationship_meta: dict[str, Any],
    input_schema: Schema,
    field_name: str,
) -> None:
    attribute = relationship_meta.get("attribute") or field_name
    if (relationship_meta.get("url_kind") or "single") == "many":
        field_obj.serialize_func = (
            lambda obj, schema_self=schema, attr=attribute, other_schema=input_schema: schema_self.get_many_url(obj, attr, other_schema)
        )
    else:
        field_obj.serialize_func = (
            lambda obj, schema_self=schema, attr=attribute, other_schema=input_schema: schema_self.get_url(obj, attr, other_schema)
        )


def _rebind_nested_field(field_obj: fields.Field, target_schema: Schema) -> None:
    if isinstance(field_obj, fields.List) and isinstance(field_obj.inner, fields.Nested):
        _assign_nested_schema(field_obj.inner, target_schema)
    elif isinstance(field_obj, fields.Nested):
        _assign_nested_schema(field_obj, target_schema)


def _rebind_cached_field(
    schema: "AutoSchema",
    field_name: str,
    field_obj: fields.Field,
    schema_loader: "Callable[..., tuple[Schema, Schema]]",
) -> None:
    metadata = getattr(field_obj, "metadata", None)
    if not metadata:
        return

    relationship_meta = metadata.get("_fa_relationship")
    if not relationship_meta:
        return

    related_model = relationship_meta.get("related_model")
    if related_model is None:
        return

    kind = relationship_meta.get("kind")
    input_schema, output_schema = schema_loader(related_model)

    if kind == "url":
        _rebind_url_field(schema, field_obj, relationship_meta, input_schema, field_name)
    elif kind == "nested":
        role = relationship_meta.get("role") or "output"
        if role == "input":
            input_schema, output_schema = schema_loader(related_model, render_nested=True)
        target_schema = output_schema if role == "output" else input_schema
        _rebind_nested_field(field_obj, target_schema)
