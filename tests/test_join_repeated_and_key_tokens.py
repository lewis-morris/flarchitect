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


def test_repeated_join_parameters_are_honoured(client):
    resp = client.get("/api/books?join=author&join=publisher&limit=1").get_json()
    assert resp["status_code"] == 200
    book = resp["value"][0]
    assert isinstance(book.get("author"), dict)
    assert isinstance(book.get("publisher"), dict)


def test_additional_keys_as_join_tokens(client):
    # author and publisher are provided as bare keys
    resp = client.get("/api/books?author&publisher&limit=1&dump=dynamic").get_json()
    assert resp["status_code"] == 200
    book = resp["value"][0]
    assert isinstance(book.get("author"), dict)
    assert isinstance(book.get("publisher"), dict)

