"""Tests for GraphQL relationship handling."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from flarchitect.graphql import create_schema_from_models


class Base(DeclarativeBase):
    """Base model for relationship tests."""


class Parent(Base):
    """Simple parent model."""

    __tablename__ = "parent"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    children: Mapped[list[Child]] = relationship("Child", back_populates="parent")


class Child(Base):
    """Simple child model."""

    __tablename__ = "child"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parent.id"))
    parent: Mapped[Parent] = relationship("Parent", back_populates="children")


def test_nested_relationship_query() -> None:
    """Nested queries should return related objects."""

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)

    parent = Parent(name="P")
    child = Child(name="C", parent=parent)
    session.add_all([parent, child])
    session.commit()

    schema = create_schema_from_models([Parent, Child], session)
    query = "{ all_parents { name children { name } } }"
    result = schema.execute(query)
    assert result.errors is None
    assert result.data == {"all_parents": [{"name": "P", "children": [{"name": "C"}]}]}

    query = "{ all_childs { name parent { name } } }"
    result = schema.execute(query)
    assert result.errors is None
    assert result.data == {"all_childs": [{"name": "C", "parent": {"name": "P"}}]}
