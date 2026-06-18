"""Tests for model inspection helper functions."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from flarchitect.database.inspections import (
    extract_relationship_info,
    get_model_columns,
    get_model_relationships,
    get_models_relationships,
)
from flarchitect.database.utils import get_models_relationships as get_models_relationships_from_utils


class Base(DeclarativeBase):
    pass


class Parent(Base):
    __tablename__ = "parent"

    id: Mapped[int] = mapped_column(primary_key=True)
    children: Mapped[list["Child"]] = relationship(back_populates="parent")


class Child(Base):
    __tablename__ = "child"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parent.id"))
    parent: Mapped[Parent] = relationship(back_populates="children")


def test_get_model_columns() -> None:
    """Ensure column names are correctly extracted."""
    assert get_model_columns(Parent, randomise=False) == ["id"]


def test_get_model_relationships() -> None:
    """Ensure related models are correctly extracted."""
    assert get_model_relationships(Parent, randomise=False) == [Child]


def test_get_models_relationships_returns_stable_relationship_metadata() -> None:
    """Ensure detailed relationship metadata keeps scalar column names."""

    relationships = get_models_relationships(Parent)

    assert relationships == [
        {
            "relationship": "children",
            "join_type": "RelationshipDirection.ONETOMANY",
            "left_column": "id",
            "right_column": "parent_id",
            "model": Child,
            "parent": Parent,
        }
    ]
    assert get_models_relationships_from_utils(Parent) == relationships


def test_extract_relationship_info_returns_empty_mapping_on_invalid_relationship() -> None:
    """Invalid relationship-like objects are ignored instead of leaking errors."""

    assert extract_relationship_info(object()) == {}
