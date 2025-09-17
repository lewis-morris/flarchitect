"""Tests for decorator behaviour with output_schema=None and kwargs filtering."""

from __future__ import annotations

from flask import Flask
from marshmallow import Schema, fields

from flarchitect import Architect
from flarchitect.utils.decorators import fields as fields_decorator


def _make_app() -> Flask:
    app = Flask(__name__)
    app.config.update(FULL_AUTO=False, API_CREATE_DOCS=False)
    return app


def test_handle_decorator_no_output_schema_returns_raw() -> None:
    app = _make_app()
    with app.app_context():
        arch = Architect(app)

    @app.get("/raw")
    @arch.schema_constructor(output_schema=None, many=False)
    def route_raw():  # type: ignore[unused-ignore]
        return {"a": 1}

    client = app.test_client()
    resp = client.get("/raw")
    assert resp.status_code == 200
    assert resp.get_json()["value"] == {"a": 1}


def test_handle_decorator_no_output_schema_many_list() -> None:
    app = _make_app()
    with app.app_context():
        arch = Architect(app)

    @app.get("/items")
    @arch.schema_constructor(output_schema=None, many=True)
    def route_items():  # type: ignore[unused-ignore]
        return [{"a": 1}, {"a": 2}]

    client = app.test_client()
    resp = client.get("/items")
    assert resp.status_code == 200
    assert resp.get_json()["value"] == [{"a": 1}, {"a": 2}]


def test_wrapper_filters_unexpected_kwargs() -> None:
    app = _make_app()
    with app.app_context():
        arch = Architect(app)

    class InSchema(Schema):
        x = fields.Integer(required=True)

        class Meta:  # provide a model attribute to trigger wrapper 'model' kwarg
            model = object

    @app.post("/echo")
    @arch.schema_constructor(input_schema=InSchema, output_schema=None)
    def echo(deserialized_data=None):  # does NOT accept **kwargs like 'model'
        return deserialized_data

    client = app.test_client()
    resp = client.post("/echo", json={"x": 7})
    assert resp.status_code == 200
    assert resp.get_json()["value"] == {"x": 7}


def test_fields_noop_when_none() -> None:
    app = _make_app()
    with app.app_context():
        arch = Architect(app)

    # fields(None) should be a no-op and not inject a 'schema' kwarg
    @fields_decorator(None)
    def handler(**kwargs):
        return kwargs

    with app.test_request_context("/noop"):
        result = handler()
        assert "schema" not in result
