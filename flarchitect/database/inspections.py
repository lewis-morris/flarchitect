"""Utility functions for inspecting SQLAlchemy models.

This module provides helper functions to extract information from SQLAlchemy
models without introducing heavy dependencies. The functions are kept in a
stand-alone module to avoid circular imports between the database operations
module and specification utilities.
"""

from __future__ import annotations

import random

from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeBase


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
