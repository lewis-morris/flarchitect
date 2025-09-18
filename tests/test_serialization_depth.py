import pytest

from demo.basic_factory.basic_factory import create_app


@pytest.fixture
def client_depth0():
    app = create_app(
        {
            "API_ADD_RELATIONS": True,
            "API_SERIALIZATION_TYPE": "json",
            "API_SERIALIZATION_DEPTH": 0,
        }
    )
    return app.test_client()


@pytest.fixture
def client_depth1():
    app = create_app(
        {
            "API_ADD_RELATIONS": True,
            "API_SERIALIZATION_TYPE": "json",
            "API_SERIALIZATION_DEPTH": 1,
        }
    )
    return app.test_client()


def test_depth_zero_degrades_nested_to_urls(client_depth0):
    resp = client_depth0.get("/api/books?limit=1").get_json()
    assert resp["status_code"] == 200
    book = resp["value"][0]
    # With depth=0 and dump=json, relations should degrade to URLs (string)
    assert isinstance(book.get("author"), str)
    assert isinstance(book.get("publisher"), str)


def test_depth_one_nests_one_level_only(client_depth1):
    resp = client_depth1.get("/api/books?limit=1").get_json()
    assert resp["status_code"] == 200
    book = resp["value"][0]
    # First level nested
    assert isinstance(book.get("author"), dict)
    # Inside author, the 'books' relation should degrade to URLs (not nested dicts)
    inner_books = book["author"].get("books")
    if inner_books is not None:  # may be URL list or omitted
        assert isinstance(inner_books, list)
        assert all(isinstance(x, str) for x in inner_books)

