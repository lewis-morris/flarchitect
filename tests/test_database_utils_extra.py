import pytest
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Integer, String

from flask import Flask

from flarchitect.database.utils import (
    create_pagination_defaults,
    extract_pagination_params,
    get_models_for_join,
    get_table_column,
    convert_value_to_type,
    get_primary_key_filters,
    list_model_columns,
    find_matching_relations,
)
from flarchitect.exceptions import CustomHTTPException


def test_extract_pagination_params_defaults_and_limit_error():
    app = Flask(__name__)
    with app.app_context():
        defaults, maxes = create_pagination_defaults()
        p, l = extract_pagination_params({})
        assert p == defaults["page"] and l == defaults["limit"]

        with pytest.raises(CustomHTTPException):
            extract_pagination_params({"limit": str(maxes["limit"] + 1)})


def test_get_models_for_join_invalid():
    def resolver(name: str):
        return None

    with pytest.raises(CustomHTTPException):
        get_models_for_join({"join": "Nope"}, resolver)
    assert get_models_for_join({}, resolver) == {}


def test_get_table_column_parsing():
    all_columns = {"users": {"id": object(), "name": object()}, "items": {"id": object()}}
    table, column, op = get_table_column("users.id__eq", all_columns)
    assert (table, column, op) == ("users", "id", "eq")
    # no operator
    table, column, op = get_table_column("name", all_columns | {"": {}})
    assert op == ""


def test_convert_value_to_type_branches():
    from sqlalchemy import Boolean, Integer, Float, Date

    assert convert_value_to_type("true", Boolean()) is True
    assert convert_value_to_type("0", Boolean()) is False
    assert convert_value_to_type("10", Integer()) == 10
    assert convert_value_to_type("2.5", Float()) == 2.5
    d = convert_value_to_type("2020-01-02", Date())
    assert str(d) == "2020-01-02"
    assert convert_value_to_type(["1", "2"], Integer()) == [1, 2]


class DBBase(DeclarativeBase):
    pass


class A(DBBase):
    __tablename__ = "a"
    id1: Mapped[int] = mapped_column(primary_key=True)
    id2: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)


def test_get_primary_key_filters_and_list_columns():
    # single column case via temporary model
    class B(DBBase):
        __tablename__ = "b"
        id: Mapped[int] = mapped_column(primary_key=True)

    assert get_primary_key_filters(B, 5) == {"id": 5}
    assert get_primary_key_filters(A, (1, 2)) == {"id1": 1, "id2": 2}
    from flask import Flask

    app = Flask(__name__)
    with app.app_context():
        cols = list_model_columns(A)
    assert "id1" in cols and "id2" in cols and "name" in cols


class C(DBBase):
    __tablename__ = "c"
    id: Mapped[int] = mapped_column(primary_key=True)
    ds: Mapped[list["D"]] = relationship("D", back_populates="c")


class D(DBBase):
    __tablename__ = "d"
    id: Mapped[int] = mapped_column(primary_key=True)
    c_id: Mapped[int] = mapped_column(ForeignKey("c.id"))
    c: Mapped[C] = relationship("C", back_populates="ds")


def test_find_matching_relations_simple():
    rels = find_matching_relations(C, D)
    # should contain relation names between C and D in either direction
    assert any(isinstance(t, tuple) and len(t) == 2 for t in rels)
