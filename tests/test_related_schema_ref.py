from flask import Flask
from marshmallow import Schema
from marshmallow_sqlalchemy.fields import Nested

from flarchitect.specs.utils import get_related_schema_name


def test_get_related_schema_name_respects_case(monkeypatch) -> None:
    monkeypatch.setenv("TYPEGUARD_DISABLE", "1")
    from demo.scaffolding.module.models import Category, Item

    class CategorySchema(Schema):
        class Meta:
            model = Category

    class ItemSchema(Schema):
        class Meta:
            model = Item

        category = Nested(CategorySchema)

    app = Flask(__name__)
    with app.app_context():
        field = ItemSchema().fields["category"]
        assert get_related_schema_name(field, Nested) == "category"
