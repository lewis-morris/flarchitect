import pytest

from demo.basic_factory.basic_factory import create_app


@pytest.fixture
def app():
    app = create_app(
        {
            "API_ALLOW_JOIN": True,
            "API_ADD_RELATIONS": True,
            "API_SERIALIZATION_TYPE": "dynamic",
        }
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_dynamic_dump_accepts_multiple_relationship_keys(client):
    # Use relationship keys (singular) comma-separated
    resp = client.get("/api/books?join=author,publisher&limit=1").get_json()
    assert resp["status_code"] == 200
    book = resp["value"][0]
    # Should embed both related objects
    assert isinstance(book.get("author"), dict)
    assert isinstance(book.get("publisher"), dict)


def test_dynamic_dump_accepts_endpoint_style_plural_names(client):
    # Use endpoint-style plural names
    resp = client.get("/api/books?join=authors,publishers&limit=1").get_json()
    assert resp["status_code"] == 200
    book = resp["value"][0]
    assert isinstance(book.get("author"), dict)
    assert isinstance(book.get("publisher"), dict)

