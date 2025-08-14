"""Utilities for converting SQLAlchemy models into GraphQL schemas."""

from __future__ import annotations
from collections.abc import Iterable
from typing import Any

import graphene
from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import DeclarativeBase, Session

__all__ = ["create_schema_from_models"]

SQLA_TYPE_MAPPING = {
    Integer: graphene.Int,
    String: graphene.String,
    Boolean: graphene.Boolean,
    Float: graphene.Float,
}


def _convert_sqla_type(column_type: Any) -> type[graphene.Scalar]:
    """Map a SQLAlchemy column type to a Graphene scalar.

    Args:
        column_type: SQLAlchemy column type instance.

    Returns:
        The corresponding Graphene scalar type. Defaults to ``graphene.String``.
    """

    for sa_type, gql_type in SQLA_TYPE_MAPPING.items():
        if isinstance(column_type, sa_type):
            return gql_type
    return graphene.String


def _model_to_object_type(model: type[DeclarativeBase]) -> type[graphene.ObjectType]:
    """Create a Graphene ``ObjectType`` for a given SQLAlchemy model.

    Args:
        model: SQLAlchemy declarative model.

    Returns:
        A dynamically generated ``ObjectType`` subclass.
    """

    fields: dict[str, Any] = {}
    for column in model.__table__.columns:  # type: ignore[attr-defined]
        gql_type = _convert_sqla_type(column.type)
        fields[column.name] = gql_type()

    return type(f"{model.__name__}Type", (graphene.ObjectType,), fields)


def create_schema_from_models(
    models: Iterable[type[DeclarativeBase]], session: Session
) -> graphene.Schema:
    """Generate a GraphQL schema exposing CRUD-style queries and mutations.

    Args:
        models: Iterable of SQLAlchemy models to expose.
        session: Active SQLAlchemy session used in resolvers.

    Returns:
        A Graphene :class:`~graphene.Schema` object with generated Query and
        Mutation types for the provided models.
    """

    object_types = {model: _model_to_object_type(model) for model in models}

    query_fields: dict[str, Any] = {}
    for model, obj_type in object_types.items():
        name = model.__tablename__
        query_fields[name] = graphene.Field(obj_type, id=graphene.Int(required=True))
        query_fields[f"all_{name}s"] = graphene.List(obj_type)

        def _resolve_one(_root, _info, id: int, model=model):
            return session.get(model, id)

        def _resolve_all(_root, _info, model=model):
            return session.query(model).all()

        query_fields[f"resolve_{name}"] = staticmethod(_resolve_one)
        query_fields[f"resolve_all_{name}s"] = staticmethod(_resolve_all)

    Query = type("Query", (graphene.ObjectType,), query_fields)

    mutation_fields: dict[str, Any] = {}
    for model, obj_type in object_types.items():
        arguments: dict[str, Any] = {}
        for column in model.__table__.columns:  # type: ignore[attr-defined]
            if column.primary_key:
                continue
            gql_type = _convert_sqla_type(column.type)
            arguments[column.name] = gql_type(required=not column.nullable)

        Arguments = type("Arguments", (), arguments)

        def _mutate(_root, _info, model=model, **kwargs):
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
