import datetime
import uuid
from typing import Any

from flask import request
from marshmallow import Schema, ValidationError, fields, post_dump, pre_dump
from marshmallow.validate import Length, Range

try:
    from numpy.lib.function_base import iterable
except Exception:
    from numpy import iterable

import sqlalchemy_utils
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
from sqlalchemy_utils.types.email import EmailType

from flarchitect.logging import logger
from flarchitect.schemas.utils import get_input_output_from_model_or_make
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
            else:
                return self.enum[value]
        except (KeyError, ValueError) as e:
            valid = [e.name if not self.by_value else e.value for e in self.enum]
            raise ValidationError(f"Invalid enum value. Expected one of: {valid}.") from e


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
    Numeric: fields.Decimal,
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


class Base(Schema):  # Inheriting from marshmallow's Schema
    def __init__(self, *args, context=None, **kwargs):
        # 1️⃣  Stash the context *before* super().__init__
        #     (marshmallow 4 no longer accepts it)
        self.context: dict = context or {}
        super().__init__(*args, **kwargs)

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

    def __init__(self, *args, render_nested=True, **kwargs):
        """Initialise the ``AutoSchema`` instance.

        Why/How:
            Configures field generation against the bound model, sets case
            conversion preferences and prepares context for nested rendering.
        """
        self.render_nested = render_nested
        self.depth = kwargs.pop("depth", 0)
        only_fields = kwargs.pop("only", None)

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

    def generate_fields(self):
        """Automatically add fields for each column and relationship in the SQLAlchemy model."""
        if not self.model:
            logger.warning("self.Meta.model is None. Skipping field generation.")
            return

        mapper = class_mapper(self.model)
        for attribute, mapper_property in mapper.all_orm_descriptors.items():
            original_attribute = attribute
            # Determine if we should skip based on the original attribute
            if self._should_skip_attribute(original_attribute):
                continue

            # Convert case, preserving leading underscore when configured to show them
            attribute = self._convert_case(original_attribute)

            # Access the actual property from the InstrumentedAttribute
            prop = getattr(mapper_property, "property", None)

            if isinstance(prop, RelationshipProperty):
                self._handle_relationship(attribute, original_attribute, mapper_property)
            elif isinstance(prop, ColumnProperty):
                self._handle_column(attribute, original_attribute, mapper_property)

            elif isinstance(mapper_property, hybrid_property):
                if get_config_or_model_meta("API_DUMP_HYBRID_PROPERTIES", model=self.model, default=True):
                    self._handle_hybrid_property(attribute, original_attribute, mapper_property)
            else:
                pass
        # print("Final fields:", self.fields)
        # print("Dump fields:", self.dump_fields)  # Should match self.fields
        # print("Load fields:", self.load_fields)  # Should match self.fields

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
        if not get_config_or_model_meta("API_ADD_RELATIONS", model=self.model, default=True):
            return
        try:
            if request.args.get("dump_relationships") in ["false", "False", "0"]:
                return
        except RuntimeError:
            # this happens when the model is outside the flask request and is expected when the schema is first
            # initialised
            pass

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

        field_type = type_mapping.get(field_type, fields.Str) if field_type else fields.Str

        # Check if the attribute has a setter method
        has_setter = (
            hasattr(type(self.model), original_attribute) and isinstance(getattr(type(self.model), original_attribute), property) and getattr(type(self.model), original_attribute).fset is not None
        )

        # If there's no setter, mark it as dump_only
        field_args = {"dump_only": not has_setter}

        self.add_to_fields(original_attribute, field_type(data_key=attribute, **field_args), load=False)

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
            field_type = type_mapping.get(type(column_type))
            if not field_type:
                logger.error(1, f"No field mapping for column type: {type(column_type)}")
                return

            # Get additional attrs for the field based on the column's properties
            field_args = self._get_column_field_attrs(original_attribute, column_type)

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

    def _get_column_field_attrs(self, original_attribute: str, column_type: Any) -> dict[str, Any]:
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
        field_args = self._add_validation(column, field_args)

        # NO UNIQUE FIELD ANY MORE??!?
        # Mark fields as unique or primary keys
        # if column.unique or column.primary_key:
        #     field_args["unique"] = True

        if column.nullable:
            field_args["allow_none"] = True

        if column.comment:
            field_args["description"] = column.comment

        return field_args

    def _add_validation(self, column: Column, field_args: dict):
        # custom validation by user
        if column.info.get("validate"):
            validator = validate_by_type(column.info.get("validate"))
            if not validator:
                raise ValueError(f"Invalid validator type: model {self.model.__name__}.{column.name} - {column.info.get('validate')}")
            field_args["validate"].append(validator)
            return field_args

        # Add validation to the field based on the column type in sql
        if hasattr(column.type, "length") and column.type.__class__ is not Enum:
            field_args["validate"].append(Length(max=column.type.length))

        if isinstance(column.type, Float | Numeric):
            field_args["validate"].append(Range(min=float("-inf"), max=float("inf")))

        if isinstance(column.type, Integer):
            field_args["validate"].append(Range(min=-2147483648, max=2147483647))

        if get_config_or_model_meta("API_AUTO_VALIDATE", model=self.model, default=True):
            # todo add more validation and test
            column_name = column.name
            format_name = column.info.get("format")
            try:
                if ("email" in column_name and column.type.python_type is str) or (format_name == "email"):
                    field_args["validate"].append(validate_by_type("email"))
                elif ("url" in column_name and column.type.python_type is str) or (format_name in ["url", "uri", "url_path"]):
                    field_args["validate"].append(validate_by_type("url"))
                elif "date" in column_name or column.type.python_type is datetime.date or format_name == "date":
                    field_args["validate"].append(validate_by_type("date"))
                elif column.type.python_type is datetime.time or format_name == "time":
                    field_args["validate"].append(validate_by_type("time"))
                elif "datetime" in column_name or column.type.python_type is datetime.datetime or format_name == "datetime":
                    field_args["validate"].append(validate_by_type("datetime"))
                elif "boolean" in column_name or column.type.python_type is bool or format_name == "boolean":
                    field_args["validate"].append(validate_by_type("boolean"))
                elif ("domain" in column_name and column.type.python_type is str) or (format_name == "domain"):
                    field_args["validate"].append(validate_by_type("domain"))
                elif format_name == "ipv4":
                    field_args["validate"].append(validate_by_type("ipv4"))
                elif format_name == "ipv6":
                    field_args["validate"].append(validate_by_type("ipv6"))
                elif format_name == "mac":
                    field_args["validate"].append(validate_by_type("mac"))
                elif format_name == "hostname":
                    field_args["validate"].append(validate_by_type("hostname"))
                elif format_name == "slug":
                    field_args["validate"].append(validate_by_type("slug"))
                elif format_name == "uuid" or column.type.python_type == uuid.UUID:
                    field_args["validate"].append(validate_by_type("uuid"))
                elif format_name == "card":
                    field_args["validate"].append(validate_by_type("card"))
                elif format_name == "country_code":
                    field_args["validate"].append(validate_by_type("country_code"))
                elif format_name == "iban":
                    field_args["validate"].append(validate_by_type("iban"))
                elif format_name == "cron":
                    field_args["validate"].append(validate_by_type("cron"))
                elif format_name == "base64":
                    field_args["validate"].append(validate_by_type("base64"))
                elif format_name == "sha224":
                    field_args["validate"].append(validate_by_type("sha224"))
                elif format_name == "sha384":
                    field_args["validate"].append(validate_by_type("sha384"))
                elif format_name == "currency":
                    field_args["validate"].append(validate_by_type("currency"))
                elif ("phone" in column_name and column.type.python_type is str) or (format_name in ["phone", "phone_number"]):
                    field_args["validate"].append(validate_by_type("phone"))
                elif "postal" in column_name or "zip" in column_name or (format_name in ["postal_code", "zip", "zipcode"]):
                    field_args["validate"].append(validate_by_type("postal_code"))
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
        related = getattr(obj, attribute)
        if isinstance(related, list):
            return [item.to_url() for item in related]
        elif related:
            return related.to_url()
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

        return getattr(obj, child_end.replace("-", "_") + "_to_url")()

    def add_relationship_field(
        self,
        attribute: str,
        original_attribute: str,
        relationship_property: RelationshipProperty,
    ) -> None:
        """Add a schema field for a SQLAlchemy relationship.

        Args:
            attribute (str): Name of the field exposed by the schema.
            original_attribute (str): Name of the relationship attribute on the model.
            relationship_property (RelationshipProperty): SQLAlchemy relationship
                descriptor.

        Returns:
            None

        Side Effects:
            Modifies schema field mappings and updates field metadata. May add
            additional load-only fields when nested writes are enabled.
        """
        allow_nested_writes = get_config_or_model_meta("ALLOW_NESTED_WRITES", model=self.model, default=False)
        max_depth = 2 if allow_nested_writes else 1
        current_depth = self.context.get("current_depth", 0)

        if current_depth >= max_depth:
            # # Exceeded maximum depth, include only the primary key reference
            # related_model = relationship_property.mapper.class_
            # primary_key = inspect(related_model).primary_key[0]
            # field_type = type_mapping.get(type(primary_key.type), fields.Integer)
            #
            # self.add_to_fields(
            #     original_attribute, field_type(data_key=attribute)
            # )
            return

        else:
            # Include the nested schema and increment the depth
            input_schema, output_schema = get_input_output_from_model_or_make(
                relationship_property.mapper.class_,
                context={"current_depth": current_depth + 1},
            )

            # Access the RelationshipProperty to get 'viewonly' and 'uselist'
            relationship_prop = relationship_property.property
            field_args = {"dump_only": not relationship_prop.viewonly}

            # Determine the serialization type
            dump_type = get_config_or_model_meta("API_SERIALIZATION_TYPE", self.model, default="url")

            if dump_type == "url":
                if relationship_prop.uselist:
                    # Serialize as a list of URLs
                    self.add_to_fields(
                        attribute,
                        fields.Function(
                            lambda obj: self.get_many_url(obj, original_attribute, input_schema),
                            **field_args,
                        ),
                        load=False,
                    )
                    field_name = attribute
                else:
                    # Serialize as a single URL
                    self.add_to_fields(
                        attribute,
                        fields.Function(
                            lambda obj: self.get_url(obj, original_attribute, input_schema),
                            **field_args,
                        ),
                        load=False,
                    )
                    field_name = attribute
            elif dump_type == "json":
                if relationship_prop.uselist:
                    # Always dump as a list of nested schemas
                    self.add_to_fields(
                        original_attribute,
                        fields.List(fields.Nested(output_schema), **field_args),
                        load=False,
                    )
                    field_name = original_attribute
                else:
                    # Always dump as a nested schema
                    self.add_to_fields(
                        original_attribute,
                        fields.Nested(output_schema, **field_args),
                        load=False,
                    )
                    field_name = original_attribute
            elif dump_type == "dynamic":
                try:
                    _ = request.args
                except RuntimeError:
                    return

                if request and request.args.get("join"):
                    joins = request.args.get("join")

                    if not joins:
                        return  # Exit early if no join parameter is provided

                    url_naming_function = get_config_or_model_meta(
                        "API_ENDPOINT_NAMER",
                        relationship_property.mapper.class_,
                        default=endpoint_namer,
                    )
                    name = url_naming_function(output_schema)

                    if not iterable(joins):
                        joins = [joins]

                    if name in joins:
                        if relationship_prop.uselist:
                            # Always dump as a list of nested schemas
                            self.add_to_fields(
                                original_attribute,
                                fields.List(fields.Nested(output_schema), **field_args),
                                load=False,
                            )
                            field_name = original_attribute
                        else:
                            # Always dump as a nested schema
                            self.add_to_fields(
                                original_attribute,
                                fields.Nested(output_schema, **field_args),
                                load=False,
                            )
                            field_name = original_attribute
                    else:
                        return
                else:
                    return

            elif dump_type == "hybrid":
                if relationship_prop.uselist:
                    # Serialize as a list of URLs
                    self.add_to_fields(
                        original_attribute,
                        fields.Function(
                            lambda obj: self.get_many_url(obj, attribute, input_schema),
                            **field_args,
                        ),
                        load=False,
                    )
                    field_name = original_attribute
                else:
                    # Serialize as a nested schema
                    self.add_to_fields(
                        original_attribute,
                        fields.Nested(output_schema, **field_args),
                        load=False,
                    )
                    field_name = original_attribute
            else:
                # Fallback to JSON serialization if an unknown dump_type is provided
                if relationship_prop.uselist:
                    self.add_to_fields(
                        original_attribute,
                        fields.List(fields.Nested(output_schema), **field_args),
                        load=False,
                    )
                    field_name = original_attribute
                else:
                    self.add_to_fields(
                        original_attribute,
                        fields.Nested(output_schema, **field_args),
                        load=False,
                    )
                    field_name = original_attribute

        self._update_field_metadata(field_name)

        if allow_nested_writes and not relationship_prop.viewonly:
            load_field = fields.List(fields.Nested(input_schema), load_only=True) if relationship_prop.uselist else fields.Nested(input_schema, load_only=True)
            self.add_to_fields(field_name, load_field, dump=False)

    def _update_field_metadata(self, attribute: str) -> None:
        """Populate OpenAPI metadata for a field.

        Args:
            attribute (str): Field name whose metadata should be updated.

        Returns:
            None

        Side Effects:
            Mutates the field's ``metadata`` dictionary in-place.
        """
        field_obj = self.fields[attribute]  # Get the Marshmallow field object
        field_meta = field_obj.metadata  # Extract the existing metadata

        # Populate metadata from SQLAlchemy column ``info`` if available.
        model_field = getattr(self.model, attribute, None)
        if model_field is not None and hasattr(model_field, "info"):
            info = model_field.info
            if desc := info.get("description"):
                field_meta.setdefault("description", desc)
            if example := info.get("example"):
                field_meta.setdefault("example", example)
            if fmt := info.get("format"):
                field_meta.setdefault("format", fmt)

        # Merge additional OpenAPI-specific metadata derived from the field
        openapi_meta_data = get_openapi_meta_data(field_obj)
        if openapi_meta_data:
            field_meta.update(openapi_meta_data)

    def dump(self, obj, *args, **kwargs):
        # print("Data before super().dump:", obj)
        result = super().dump(obj, *args, **kwargs) if self.fields else self.__class__(context=self.context).dump(obj, *args, **kwargs)
        # print("Data after super().dump:", result)
        return result
