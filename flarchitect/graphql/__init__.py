"""Helpers for turning SQLAlchemy models into GraphQL schemas.

This module provides a small bridge between SQLAlchemy and the ``graphene``
library. Given a list of declarative models and an active
``sqlalchemy.orm.Session`` it dynamically builds :class:`graphene.ObjectType`
classes, query fields and mutation fields that expose basic CRUD operations.

The default :data:`SQLA_TYPE_MAPPING` covers common column types such as
``Integer``, ``String``, ``Boolean``, ``Float``, ``Date``, ``DateTime``,
``Numeric``, ``JSON`` and ``UUID``. Custom or proprietary SQLAlchemy types can
be mapped to Graphene scalars by supplying a ``type_mapping`` override to
:func:`create_schema_from_models`.

Example:
    >>> from sqlalchemy import Integer, String
    >>> from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
    >>> class Base(DeclarativeBase):
    ...     pass
    >>> class Item(Base):
    ...     __tablename__ = "item"
    ...     id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ...     name: Mapped[str] = mapped_column(String)
    >>> session = Session(...)  # an engine bound session
    >>> schema = create_schema_from_models([Item], session)
    >>> query = "{ all_items { id name } }"
    >>> schema.execute_sync(query).data
    {'all_items': []}

The schema exposes ``Item`` through ``item`` and ``all_items`` queries as well
as a ``create_item`` mutation that accepts the model's columns as arguments.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import graphene
from sqlalchemy import (
    JSON,
    UUID,
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Session

__all__ = ["create_schema_from_models"]

# Mapping of common SQLAlchemy column types to their Graphene scalar
# counterparts. Extend this dictionary if your models use additional types.
SQLA_TYPE_MAPPING: dict[type, type[graphene.Scalar]] = {
    Integer: graphene.Int,
    String: graphene.String,
    Boolean: graphene.Boolean,
    Float: graphene.Float,
    Date: graphene.Date,
    DateTime: graphene.DateTime,
    Numeric: graphene.Decimal,
    JSON: graphene.JSONString,
    UUID: graphene.UUID,
}


def _convert_sqla_type(column_type: Any, type_mapping: dict[type, type[graphene.Scalar]]) -> type[graphene.Scalar]:
    """Map a SQLAlchemy column type to a Graphene scalar.

    Args:
        column_type: SQLAlchemy column type instance.
        type_mapping: Mapping of SQLAlchemy types to Graphene scalars.

    Returns:
        Graphene scalar type. Defaults to :class:`graphene.String` when no
        explicit mapping is found.

    Examples:
        >>> from sqlalchemy import Integer
        >>> _convert_sqla_type(Integer(), SQLA_TYPE_MAPPING) is graphene.Int
        True
    """

    for sa_type, gql_type in type_mapping.items():
        if isinstance(column_type, sa_type):
            return gql_type
    return graphene.String


def _model_to_object_type(model: type[DeclarativeBase], type_mapping: dict[type, type[graphene.Scalar]]) -> type[graphene.ObjectType]:
    """Create a Graphene ``ObjectType`` for a given SQLAlchemy model.

    The function inspects the model's table and converts each column into a
    GraphQL field using :func:`_convert_sqla_type`.

    Args:
        model: SQLAlchemy declarative model.
        type_mapping: Mapping of SQLAlchemy types to Graphene scalars.

    Returns:
        A dynamically generated ``ObjectType`` subclass whose fields mirror the
        model's columns.

    Examples:
        >>> class User(Base):
        ...     __tablename__ = "user"
        ...     id: Mapped[int] = mapped_column(primary_key=True)
        >>> UserType = _model_to_object_type(User, SQLA_TYPE_MAPPING)
        >>> issubclass(UserType, graphene.ObjectType)
        True
    """

    fields: dict[str, Any] = {}
    for column in model.__table__.columns:  # type: ignore[attr-defined]
        gql_type = _convert_sqla_type(column.type, type_mapping)
        fields[column.name] = gql_type()

    return type(f"{model.__name__}Type", (graphene.ObjectType,), fields)


def create_schema_from_models(
    models: Iterable[type[DeclarativeBase]],
    session: Session,
    type_mapping: dict[type, type[graphene.Scalar]] | None = None,
) -> graphene.Schema:
    """Generate a GraphQL schema exposing CRUD-style queries and mutations.

    Each provided model receives two query fields:

    * ``<table_name>(id: ID)`` – fetch a single row by primary key.
    * ``all_<table_name>s`` – fetch rows with optional filters, ``limit`` and
      ``offset`` arguments.

    And one mutation field:

    * ``create_<table_name>(**columns)`` – insert a new row.

    Args:
        models: Iterable of SQLAlchemy models to expose.
        session: Active SQLAlchemy session used in resolvers.
        type_mapping: Optional mapping of SQLAlchemy types to Graphene scalars
            that overrides :data:`SQLA_TYPE_MAPPING`.

    Returns:
        A Graphene :class:`~graphene.Schema` with the generated ``Query`` and
        ``Mutation`` types.

    Examples:
        >>> schema = create_schema_from_models([Item], session)
        >>> result = schema.execute_sync('{ all_items { id } }')
        >>> result.data['all_items']
        []
    """

    mapping = {**SQLA_TYPE_MAPPING, **(type_mapping or {})}
    object_types = {model: _model_to_object_type(model, mapping) for model in models}

    # Build query fields for single-record and list retrieval.
    query_fields: dict[str, Any] = {}
    for model, obj_type in object_types.items():
        name = model.__tablename__
        query_fields[name] = graphene.Field(obj_type, id=graphene.Int(required=True))

        # Collect filterable columns for list queries and add pagination args.
        list_args: dict[str, Any] = {}
        for column in model.__table__.columns:  # type: ignore[attr-defined]
            gql_type = _convert_sqla_type(column.type)
            list_args[column.name] = gql_type()
        list_args["limit"] = graphene.Int()
        list_args["offset"] = graphene.Int()
        query_fields[f"all_{name}s"] = graphene.List(obj_type, **list_args)

        def _resolve_one(_root, _info, id: int, model=model):
            """Resolver for fetching a single record by ID."""

            return session.get(model, id)

        def _resolve_all(_root, _info, model=model, **kwargs):
            """Resolver for fetching records with optional filters and pagination."""

            query = session.query(model)
            pk = list(model.__table__.primary_key.columns)[0]  # type: ignore[attr-defined]
            query = query.order_by(pk)

            limit = kwargs.pop("limit", None)
            offset = kwargs.pop("offset", None)
            for column, value in kwargs.items():
                if value is not None:
                    query = query.filter(getattr(model, column) == value)

            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            return query.all()

        query_fields[f"resolve_{name}"] = staticmethod(_resolve_one)
        query_fields[f"resolve_all_{name}s"] = staticmethod(_resolve_all)

    Query = type("Query", (graphene.ObjectType,), query_fields)

    # Build mutation fields for record creation.
    mutation_fields: dict[str, Any] = {}
    for model, obj_type in object_types.items():
        arguments: dict[str, Any] = {}
        for column in model.__table__.columns:  # type: ignore[attr-defined]
            if column.primary_key:
                continue
            gql_type = _convert_sqla_type(column.type, mapping)
            arguments[column.name] = gql_type(required=not column.nullable)

        Arguments = type("Arguments", (), arguments)

        def _mutate(_root, _info, model=model, **kwargs):
            """Resolver creating and persisting a new record."""

            instance = model(**kwargs)
            session.add(instance)
            session.commit()
            return instance

        mutation = type(
            f"Create{model.__name__}",
            (graphene.Mutation,),
            {
                "Arguments": Arguments,
                "Output": obj_type,
                "mutate": staticmethod(_mutate),
            },
        )

        mutation_fields[f"create_{model.__tablename__}"] = mutation.Field()

    Mutation = type("Mutation", (graphene.ObjectType,), mutation_fields)

    return graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)
