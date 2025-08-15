import warnings

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from flask import Flask
from marshmallow import Schema, fields

from flarchitect.specs.generator import register_schemas


class CategorySchema(Schema):
    """Simple schema for testing duplicate registration."""

    id = fields.Int()


def test_register_schemas_avoids_duplicates():
    """Registering the same schema twice should not emit a warning."""
    app = Flask(__name__)
    spec = APISpec(
        title="Test",
        version="1.0.0",
        openapi_version="3.0.2",
        plugins=[MarshmallowPlugin()],
    )
    schema = CategorySchema()

    with app.app_context(), warnings.catch_warnings(record=True) as caught:
        register_schemas(spec, schema)
        register_schemas(spec, schema)

    assert not any("has already been added to the spec" in str(w.message) for w in caught)


class ItemSchema(Schema):
    id = fields.Int()


def test_register_schemas_preserves_name_and_case():
    app = Flask(__name__)
    spec = APISpec(
        title="Test",
        version="1.0.0",
        openapi_version="3.0.2",
        plugins=[MarshmallowPlugin()],
    )
    schema = ItemSchema()

    with app.app_context():
        register_schemas(spec, schema)
        register_schemas(spec, schema)

    assert schema.__class__.__name__ == "ItemSchema"
    assert "item" in spec.components.schemas
    assert "patchItem" not in spec.components.schemas
