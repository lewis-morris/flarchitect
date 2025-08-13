import pytest
from marshmallow import fields

from demo.basic_factory.basic_factory import create_app
from demo.basic_factory.basic_factory.models import Book
from flarchitect.schemas.utils import get_input_output_from_model_or_make


@pytest.fixture
def app():
    app = create_app(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
            "API_ALLOW_NESTED_WRITES": True,
        }
    )
    with app.app_context():
        yield app


def test_auto_schema_loads_nested_relationship(app):
    """Ensure nested relationship data can be deserialized."""
    with app.app_context():
        _, schema = get_input_output_from_model_or_make(Book)
        assert isinstance(schema.dump_fields["author"], fields.Function)
        assert isinstance(schema.load_fields["author"], fields.Nested)
        data = {
            "title": "My Book",
            "isbn": "12345",
            "publication_date": "2024-01-01",
            "author_id": 1,
            "publisher_id": 1,
            "author": {
                "first_name": "John",
                "last_name": "Doe",
                "biography": "bio",
                "date_of_birth": "1980-01-01",
                "nationality": "US",
            },
        }
        result = schema.load(data)
        assert result["author"]["first_name"] == "John"
