"""Tests for the documentation bundle endpoint."""

from __future__ import annotations

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields
from sqlalchemy import Column, Integer, String
from sqlalchemy.pool import StaticPool

from flarchitect import Architect


db = SQLAlchemy()


class BaseModel(db.Model):
    __abstract__ = True


class Widget(BaseModel):
    __tablename__ = "widgets"

    id = Column(Integer, primary_key=True)
    name = Column(String)

    class Meta:
        pass


class WidgetSchema(Schema):
    id = fields.Int()
    name = fields.Str()


def _make_app():
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_ENGINE_OPTIONS={"poolclass": StaticPool},
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        API_CREATE_DOCS=False,
        API_SCHEMA_DISCOVERY_AUTH=False,
        API_DOCS_BUNDLE_AUTH=False,
    )
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

        @app.get("/api/widgets")
        @architect.schema_constructor(output_schema=WidgetSchema, auth=False)
        def manual_widgets():  # manual override to create conflict
            return []

        app.extensions["_created_routes_snapshot"] = architect.api.created_routes

    return app


def test_docs_bundle_highlights_conflicts():
    app = _make_app()
    client = app.test_client()

    resp = client.get("/docs/bundle")
    assert resp.status_code == 200
    payload = resp.get_json()["value"]

    routes = payload["routes"]
    urls = [route["url"] for route in routes]
    assert "/api/widgets" in urls, routes

    manual_route = next(route for route in routes if route["blueprint"] == "manual_widgets")
    assert manual_route["auto_generated"] is False

    auto_routes = [route for route in routes if route["auto_generated"]]
    assert auto_routes
