"""Tests for the runtime schema discovery endpoint."""

from __future__ import annotations

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.pool import StaticPool

from flarchitect import Architect


db = SQLAlchemy()


class BaseModel(db.Model):
    __abstract__ = True


class Author(BaseModel):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    books = relationship("Book", back_populates="author")


class Book(BaseModel):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("authors.id"))
    author = relationship("Author", back_populates="books")


def _create_app(**config):
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={"poolclass": StaticPool},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        API_CREATE_DOCS=False,
        API_SCHEMA_DISCOVERY_AUTH=False,
        FULL_AUTO=True,
        API_PREFIX="/api",
    )
    app.config.update(config)
    db.init_app(app)

    architect = Architect()
    with app.app_context():
        architect.init_app(
            app,
            api_full_auto=True,
            api_base_model=BaseModel,
            session=db.session,
        )
        db.create_all()

    return app


def test_schema_discovery_lists_fields_relationships():
    app = _create_app()
    client = app.test_client()

    resp = client.get("/schema/discovery")
    assert resp.status_code == 200

    payload = resp.get_json()
    assert payload is not None
    data = payload["value"]

    assert "models" in data
    names = {model["name"] for model in data["models"]}
    assert {"Author", "Book"}.issubset(names)

    author = next(model for model in data["models"] if model["name"] == "Author")
    field_names = {field["name"] for field in author["fields"]}
    assert {"id", "name"}.issubset(field_names)

    relationships = {rel["name"] for rel in author["relationships"]}
    assert "books" in relationships

    join_paths = {path["path"] for path in author["join_paths"]}
    assert "books" in join_paths
    assert "books.author" in join_paths  # depth traversal

    assert "operators" in data and set(data["operators"]) >= {"eq", "ne"}
    assert "aggregates" in data and "count" in data["aggregates"]


def test_schema_discovery_model_filter_and_depth():
    app = _create_app(API_SCHEMA_DISCOVERY_MAX_DEPTH=3)
    client = app.test_client()

    # Filter to a single model (case-insensitive)
    resp = client.get("/schema/discovery", query_string={"model": "author"})
    data = resp.get_json()["value"]
    assert len(data["models"]) == 1
    assert data["models"][0]["name"] == "Author"

    # Depth override limits nested join paths
    resp_depth = client.get("/schema/discovery", query_string={"model": "author", "depth": 1})
    author_paths = {p["path"] for p in resp_depth.get_json()["value"]["models"][0]["join_paths"]}
    assert "books" in author_paths
    assert "books.author" not in author_paths
