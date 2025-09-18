import pytest

from demo.basic_factory.basic_factory import create_app


@pytest.fixture
def app():
    app = create_app(
        {
            "API_ALLOW_JOIN": True,
            # Relations disabled by default; dynamic + join should still inline requested ones
            "API_ADD_RELATIONS": False,
            # Keep default output as URL to ensure per-request override is used
            "API_SERIALIZATION_TYPE": "url",
            "API_SERIALIZATION_DEPTH": 1,
        }
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_dynamic_dump_inlines_when_relations_disabled_single_param(client):
    resp = client.get("/api/books?dump=dynamic&join=author,publisher&limit=1").get_json()
    assert resp["status_code"] == 200
    book = resp["value"][0]
    assert isinstance(book.get("author"), dict)
    assert isinstance(book.get("publisher"), dict)


def test_dynamic_dump_inlines_when_relations_disabled_repeated_params(client):
    resp = client.get("/api/books?dump=dynamic&join=author&join=publisher&limit=1").get_json()
    assert resp["status_code"] == 200
    book = resp["value"][0]
    assert isinstance(book.get("author"), dict)
    assert isinstance(book.get("publisher"), dict)


def test_dynamic_dump_inlines_when_relations_disabled_additional_keys(client):
    # Use bare keys matching relationship names
    resp = client.get("/api/books?dump=dynamic&author&publisher&limit=1").get_json()
    assert resp["status_code"] == 200
    book = resp["value"][0]
    assert isinstance(book.get("author"), dict)
    assert isinstance(book.get("publisher"), dict)
