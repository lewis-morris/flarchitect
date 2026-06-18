"""Utility functions for inspecting SQLAlchemy models.

This module provides helper functions to extract information from SQLAlchemy
models without introducing heavy dependencies. The functions are kept in a
stand-alone module to avoid circular imports between the database operations
module and specification utilities.
"""

from __future__ import annotations

import random
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase, RelationshipProperty

from flarchitect.logging import logger


def get_model_relationships(model: DeclarativeBase, randomise: bool = True) -> list[type[DeclarativeBase]]:
    """Extract relationship models from a SQLAlchemy model.

    Args:
        model: The SQLAlchemy model to inspect.
        randomise: If ``True`` the order of the relationships is randomised.

    Returns:
        List of related model classes.
    """
    relationships = [rel.mapper.class_ for rel in inspect(model).relationships]
    if randomise:
        random.shuffle(relationships)
    return relationships


def get_models_relationships(model: type[DeclarativeBase]) -> list[dict[str, Any]]:
    """Return detailed relationship metadata for a SQLAlchemy model."""

    if not model:
        return []

    relationships: list[dict[str, Any]] = []
    for relationship in inspect(model).relationships:
        relationship_info = extract_relationship_info(relationship)
        if not relationship_info:
            continue
        relationships.append(relationship_info)
        logger.debug(
            4,
            f"Added |{model.__name__}| relationship with |{relationship_info['model'].__name__}| "
            f"via columns {relationship_info['left_column']} to {relationship_info['right_column']}.",
        )
    return relationships


def _first_column_name(columns: list[str]) -> str | None:
    """Return the first column name from a relationship pair, if present."""

    return columns[0] if columns else None


def extract_relationship_info(rel: RelationshipProperty) -> dict[str, Any]:
    """Extract detailed information from a SQLAlchemy relationship property."""

    try:
        left_columns = [local.name for local, _ in rel.local_remote_pairs]
        right_columns = [remote.name for _, remote in rel.local_remote_pairs]

        return {
            "relationship": rel.key,
            "join_type": str(rel.direction),
            "left_column": _first_column_name(left_columns),
            "right_column": _first_column_name(right_columns),
            "model": rel.mapper.class_,
            "parent": rel.parent.class_,
        }
    except Exception as exc:
        logger.error(1, f"Error extracting relationship info: {exc}")
        return {}


def get_model_columns(model: DeclarativeBase, randomise: bool = True) -> list[str]:
    """Return a list of column names for a SQLAlchemy model.

    Args:
        model: The SQLAlchemy model to inspect.
        randomise: If ``True`` the order of the column names is randomised.

    Returns:
        List of column names defined on ``model``.
    """
    columns = [column.name for column in inspect(model).mapper.columns]
    if randomise:
        random.shuffle(columns)
    return columns


def extract_model_attributes(model: type[DeclarativeBase]) -> tuple[set[str], set[str]]:
    """Return model column keys and non-column ORM attribute keys."""

    inspector = inspect(model)
    model_keys = {column.key for column in inspector.columns}
    model_properties = set(inspector.attrs.keys()).difference(model_keys)
    return model_keys, model_properties
