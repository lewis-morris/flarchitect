"""Tests for model inspection helper functions."""

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from flarchitect.database.inspections import (
    get_model_columns,
    get_model_relationships,
)


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
