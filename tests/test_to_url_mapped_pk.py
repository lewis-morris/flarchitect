"""Tests for to_url using mapped primary key (Column.key vs Column.name)."""

from __future__ import annotations

from flask import Flask
from sqlalchemy import Column, Integer
from sqlalchemy.orm import DeclarativeBase

from flarchitect import Architect
from flarchitect.core.routes import RouteCreator


class _Base(DeclarativeBase):
    pass


class Foo(_Base):
    __tablename__ = "foo"
    # Database column name differs from Python attribute; Column.key will be "id"
    id = Column("foo_id", Integer, primary_key=True)


def test_to_url_uses_key_for_mapped_pk() -> None:
    app = Flask(__name__)
    app.config.update(FULL_AUTO=False, API_CREATE_DOCS=False)
    with app.app_context():
        arch = Architect(app)

        # Attach the to_url helper without generating routes
        rc = RouteCreator(architect=arch, app=app, api_full_auto=False)
        rc._add_self_url_function_to_model(Foo)

    f = Foo(id=123)
    # Endpoint naming defaults to pluralised kebab-case -> "foos"
    with app.app_context():
        assert f.to_url().endswith("/foos/123")
