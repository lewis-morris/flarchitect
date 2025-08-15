"""Tests for GraphQL relationships."""

from __future__ import annotations

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from flarchitect import Architect
from flarchitect.graphql import create_schema_from_models


class Base(DeclarativeBase):
    """Base declarative model used for relationship tests."""


db = SQLAlchemy(model_class=Base)


class Parent(db.Model):
    """Parent model with a one-to-many relationship to :class:`Child`."""

    __tablename__ = "parent"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    children: Mapped[list[Child]] = relationship(back_populates="parent")


class Child(db.Model):
    """Child model pointing back to :class:`Parent`."""

    __tablename__ = "child"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    parent_id: Mapped[int] = mapped_column(ForeignKey("parent.id"))
    parent: Mapped[Parent] = relationship(back_populates="children")


def create_app() -> Flask:
    """Create a Flask app configured for testing relationships."""

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        API_TITLE="Test API",
        API_VERSION="1.0",
        API_BASE_MODEL=Base,
    )

    with app.app_context():
        db.init_app(app)
        db.create_all()
        arch = Architect(app)
        schema = create_schema_from_models([Parent, Child], db.session)
        arch.init_graphql(schema=schema)

    return app


def test_nested_relationship_query() -> None:
    """Ensure nested relationship queries return expected data."""

    app = create_app()
    client = app.test_client()

    mutation_parent = {"query": 'mutation { create_parent(name: "P1") { id } }'}
    resp = client.post("/graphql", json=mutation_parent)
    parent_id = resp.json["data"]["create_parent"]["id"]

    mutation_child = {
        "query": f"mutation {{ create_child(parent_id: {parent_id}) {{ id parent {{ id }} }} }}"
    }
    resp = client.post("/graphql", json=mutation_child)
    assert resp.json["data"]["create_child"]["parent"]["id"] == parent_id

    query = {"query": "{ all_parents { id children { id parent { id } } } }"}
    resp = client.post("/graphql", json=query)
    assert resp.status_code == 200
    assert (
        resp.json["data"]["all_parents"][0]["children"][0]["parent"]["id"] == parent_id
    )
