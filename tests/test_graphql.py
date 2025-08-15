"""Tests for GraphQL integration."""

from __future__ import annotations

import graphene
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from graphql import GraphQLInt
from sqlalchemy import JSON, Date, DateTime, Integer, Numeric, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import TypeDecorator

from flarchitect import Architect
from flarchitect.graphql import (
    SQLA_TYPE_MAPPING,
    _convert_sqla_type,
    create_schema_from_models,
)


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


def test_extended_type_mapping() -> None:
    """Ensure additional SQLAlchemy types map to correct Graphene scalars."""

    assert _convert_sqla_type(Date(), SQLA_TYPE_MAPPING) is graphene.Date
    assert _convert_sqla_type(DateTime(), SQLA_TYPE_MAPPING) is graphene.DateTime
    assert _convert_sqla_type(Numeric(), SQLA_TYPE_MAPPING) is graphene.Decimal
    assert _convert_sqla_type(JSON(), SQLA_TYPE_MAPPING) is graphene.JSONString


class CustomInt(TypeDecorator):
    """Custom SQLAlchemy type for override tests."""

    impl = Integer


class CustomModel(db.Model):
    """Model using a custom type for testing overrides."""

    __tablename__ = "custom_model"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    value: Mapped[int] = mapped_column(CustomInt)


def test_type_mapping_override() -> None:
    """Allow overriding default type mapping when building schemas."""

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    schema = create_schema_from_models(
        [CustomModel], session, type_mapping={CustomInt: graphene.Int}
    )
    field_type = schema.graphql_schema.get_type("CustomModelType").fields["value"].type
    assert field_type is GraphQLInt


def test_graphql_filters_and_pagination() -> None:
    """Ensure filters and pagination work for list queries."""

    app = create_app()
    client = app.test_client()

    response = client.get("/graphql")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert "GraphiQL" in response.get_data(as_text=True)

    for name in ["Foo", "Bar", "Baz"]:
        mutation = {
            "query": f'mutation {{ create_item(name: "{name}") {{ id name }} }}'
        }
        response = client.post("/graphql", json=mutation)
        assert response.status_code == 200

    query = {"query": '{ all_items(name: "Bar") { name } }'}
    response = client.post("/graphql", json=query)
    assert response.status_code == 200
    assert response.json["data"]["all_items"] == [{"name": "Bar"}]


def test_update_and_delete_mutations() -> None:
    """Ensure update and delete mutations behave correctly."""

    app = create_app()
    client = app.test_client()

    mutation = {"query": 'mutation { create_item(name: "Foo") { id name } }'}
    response = client.post("/graphql", json=mutation)
    item_id = response.json["data"]["create_item"]["id"]

    mutation = {
        "query": f'mutation {{ update_item(id: {item_id}, name: "Bar") {{ id name }} }}'
    }
    response = client.post("/graphql", json=mutation)
    assert response.status_code == 200
    assert response.json["data"]["update_item"]["name"] == "Bar"

    mutation = {"query": f"mutation {{ delete_item(id: {item_id}) }}"}
    response = client.post("/graphql", json=mutation)
    assert response.status_code == 200
    assert response.json["data"]["delete_item"] is True

    query = {"query": "{ all_items { id } }"}
    response = client.post("/graphql", json=query)
    assert response.json["data"]["all_items"] == []
