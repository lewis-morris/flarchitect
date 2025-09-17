from __future__ import annotations

import graphene
from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import TypeDecorator
from sqlalchemy import create_engine

from flarchitect.graphql import _convert_sqla_type, create_schema_from_models


class Base(DeclarativeBase):
    pass


class Unknown(TypeDecorator):
    impl = Integer


def test_convert_sqla_type_fallback_to_string() -> None:
    # Unknown (unmapped) types should map to graphene.String
    assert _convert_sqla_type(Unknown(), {}) is graphene.String


class Foo(Base):
    __tablename__ = "foo"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Integer)


def test_update_delete_when_missing_row() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    schema = create_schema_from_models([Foo], session)

    # Update non-existent returns null
    result = schema.execute("mutation { update_foo(id: 999, name: 1) { id } }")
    assert result.errors is None
    assert result.data == {"update_foo": None}

    # Delete non-existent returns false
    result = schema.execute("mutation { delete_foo(id: 999) }")
    assert result.errors is None
    assert result.data == {"delete_foo": False}

