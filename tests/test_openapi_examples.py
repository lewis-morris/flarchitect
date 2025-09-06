from __future__ import annotations

from marshmallow import Schema, fields

from demo.basic_factory.basic_factory import create_app
from flarchitect.specs.utils import get_openapi_meta_data


class SampleSchema(Schema):
    int_field = fields.Integer()
    float_field = fields.Float()
    decimal_field = fields.Decimal()
    bool_field = fields.Boolean()


def test_get_openapi_meta_data_defaults() -> None:
    """get_openapi_meta_data returns placeholder examples when none supplied."""
    schema = SampleSchema()
    assert get_openapi_meta_data(schema.fields["int_field"])["example"] == 1
    assert get_openapi_meta_data(schema.fields["float_field"])["example"] == 1.23
    assert get_openapi_meta_data(schema.fields["decimal_field"])["example"] == 9.99
    assert get_openapi_meta_data(schema.fields["bool_field"])["example"] is True


def test_spec_has_default_examples() -> None:
    """Generated OpenAPI spec includes default examples for numeric fields."""
    app = create_app()
    client = app.test_client()
    spec = client.get("/docs/apispec.json").get_json()
    author_id = spec["components"]["schemas"]["author"]["properties"]["id"]["example"]
    rating = spec["components"]["schemas"]["review"]["properties"]["rating"]["example"]
    assert author_id == 1
    assert rating == 1.23


def test_config_override_in_spec() -> None:
    """Config overrides take precedence over default example placeholders."""
    app = create_app({"API_OPENAPI_FIELD_EXAMPLE_DEFAULTS": {"Integer": 7}})
    with app.app_context():
        assert get_openapi_meta_data(fields.Integer())["example"] == 7
