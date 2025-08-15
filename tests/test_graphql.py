"""Tests for GraphQL integration."""

from __future__ import annotations

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect
from flarchitect.graphql import create_schema_from_models


class Base(DeclarativeBase):
    """Base declarative model used in tests."""


db = SQLAlchemy(model_class=Base)


class Item(db.Model):
    """Simple item model for GraphQL tests."""

    __tablename__ = "item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)


def create_app() -> Flask:
    """Create a Flask app configured for testing."""

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
        schema = create_schema_from_models([Item], db.session)
        arch.init_graphql(schema=schema)

    return app


def test_graphql_query_and_mutation() -> None:
    """Ensure basic query and mutation operations work."""

    app = create_app()
    client = app.test_client()

    mutation = {"query": 'mutation { create_item(name: "Foo") { id name } }'}
    response = client.post("/graphql", json=mutation)
    assert response.status_code == 200
    assert response.json["data"]["create_item"]["name"] == "Foo"

    query = {"query": "{ all_items { name } }"}
    response = client.post("/graphql", json=query)
    assert response.status_code == 200
    assert response.json["data"]["all_items"] == [{"name": "Foo"}]

    spec_resp = client.get("/openapi.json")
    assert "/graphql" in spec_resp.get_json()["paths"]


def test_graphql_update_and_delete() -> None:
    """Verify update and delete mutations modify the data store."""

    app = create_app()
    client = app.test_client()

    # seed with an item
    client.post(
        "/graphql", json={"query": 'mutation { create_item(name: "Foo") { id } }'}
    )

    update_mutation = {
        "query": 'mutation { update_item(id: 1, name: "Bar") { id name } }'
    }
    response = client.post("/graphql", json=update_mutation)
    assert response.status_code == 200
    assert response.json["data"]["update_item"] == {"id": 1, "name": "Bar"}

    delete_mutation = {"query": "mutation { delete_item(id: 1) }"}
    response = client.post("/graphql", json=delete_mutation)
    assert response.status_code == 200
    assert response.json["data"]["delete_item"] is True

    # ensure record removed
    query = {"query": "{ all_items { id } }"}
    response = client.post("/graphql", json=query)
    assert response.status_code == 200
    assert response.json["data"]["all_items"] == []
