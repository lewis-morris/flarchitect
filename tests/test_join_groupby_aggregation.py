import pytest

from demo.basic_factory.basic_factory import create_app
from demo.basic_factory.basic_factory.extensions import db
from demo.basic_factory.basic_factory.models import Book
from flarchitect.database.operations import CrudService


@pytest.fixture
def app():
    app = create_app(
        {
            "API_ALLOW_JOIN": True,
            "API_ALLOW_GROUPBY": True,
            "API_ALLOW_AGGREGATION": True,
        }
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_join_allows_related_fields(client):
    author = client.get("/api/authors/1").get_json()["value"]
    resp = client.get(f"/api/books?join=author&author.id__eq={author['id']}")
    assert resp.status_code == 200
    books = resp.get_json()["value"]
    assert books and all(book["author_id"] == author["id"] for book in books)


def test_groupby_with_aggregation(client):
    with client.application.app_context():
        service = CrudService(Book, db.session)
        query = service.filter_query_from_args({"groupby": "author_id", "id|book_count__count": "1"})
        rows = query.all()
        assert rows and hasattr(rows[0], "book_count")
