from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from flarchitect.core.utils import (
    SQLALCHEMY_TO_FLASK_CONVERTER,
    get_foreign_key_to_parent,
    get_pk,
    get_primary_key_info,
    get_url_pk,
)


class Base(DeclarativeBase):
    pass


assoc_table = Table(
    "assoc",
    Base.metadata,
    Column("parent_id", ForeignKey("parent.id"), primary_key=True),
    Column("child_id", ForeignKey("child.id"), primary_key=True),
)


class Parent(Base):
    __tablename__ = "parent"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    children = relationship("Child", secondary=assoc_table, back_populates="parents")


class Child(Base):
    __tablename__ = "child"
    id: Mapped[int] = mapped_column(primary_key=True)
    parents = relationship("Parent", secondary=assoc_table, back_populates="children")


class BoolPK(Base):
    __tablename__ = "boolpk"
    id: Mapped[bool] = mapped_column(Boolean, primary_key=True)


class MultiPK(Base):
    __tablename__ = "multipk"
    a: Mapped[int] = mapped_column(primary_key=True)
    b: Mapped[int] = mapped_column(primary_key=True)


def test_get_pk_and_url_pk_and_primary_key_info():
    col = get_pk(Parent)
    assert col.key == "id"
    url_pk = get_url_pk(Parent)
    assert url_pk == "<int:id>"
    info = get_primary_key_info(Parent)
    assert info == ("id", "int")


def test_get_foreign_key_to_parent_via_association():
    child_fk, parent_fk = get_foreign_key_to_parent(Child, Parent)
    assert {child_fk, parent_fk} == {"child_id", "parent_id"}


def test_primary_key_info_boolean_and_converter_mapping():
    name, conv = get_primary_key_info(BoolPK)
    assert name == "id"
    assert conv == "int"  # Boolean represented as 0/1 in URL converters
    # ensure converter mapping contains expected primitive fallbacks
    assert SQLALCHEMY_TO_FLASK_CONVERTER[int] == "int"
    assert SQLALCHEMY_TO_FLASK_CONVERTER[str] == "string"


import pytest


def test_get_pk_raises_for_composite_key():
    with pytest.raises(ValueError):
        get_pk(MultiPK)


def test_get_foreign_key_to_parent_none_when_no_association():
    class Lonely(Base):
        __tablename__ = "lonely"
        id: Mapped[int] = mapped_column(primary_key=True)

    assert get_foreign_key_to_parent(Lonely, Parent) is None
