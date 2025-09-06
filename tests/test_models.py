import pytest

from demo.model_extension.model import create_app
from demo.model_extension.model.models import Author


@pytest.fixture
def app():
    app = create_app(
        {
            "API_TITLE": "Automated test",
            "API_VERSION": "0.2.0",
            "API_IGNORE_UNDERSCORE_ATTRIBUTES": True,
            # Other configurations specific to this test
        }
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_examples_data_type_and_desc(client):
    info = Author.date_of_birth.info
    description = info.get("description")
    format_ = info.get("format")
    example = info.get("example")

    swagger_response = client.get("/docs/apispec.json").json
    author_schema = swagger_response["components"]["schemas"]["author"]["properties"]["date_of_birth"]

    assert author_schema["format"] == format_
    assert author_schema["description"] == description
    assert author_schema["example"] == example
