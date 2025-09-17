import pytest

from demo.basic_factory.basic_factory import create_app
from demo.basic_factory.basic_factory.extensions import db
from demo.basic_factory.basic_factory.models import Book, Author, Publisher
from flarchitect.schemas.utils import get_input_output_from_model_or_make


@pytest.fixture()
def app_relations_depth1():
    app = create_app(
        {
            # Ensure relations are enabled and a positive depth triggers eager loading
            "API_ADD_RELATIONS": True,
            "API_SERIALIZATION_DEPTH": 1,
            # Keep default "url" serialization so relations are present without payload bloat
            "API_SERIALIZATION_TYPE": "url",
        }
    )
    return app


def test_get_endpoints_with_relations_return_200(app_relations_depth1):
    client = app_relations_depth1.test_client()

    # Many endpoint
    r_books = client.get("/api/books")
    assert r_books.status_code == 200
    data_books = r_books.get_json()
    assert "value" in data_books
    # Relations should be materialised as URLs at depth 1 (author/publisher)
    if data_books["value"]:
        first = data_books["value"][0]
        # Author/Publisher fields present (URL or None)
        assert "author" in first
        assert "publisher" in first

    # Single endpoint
    r_author = client.get("/api/authors/1")
    assert r_author.status_code == 200

    # Another many endpoint
    r_pubs = client.get("/api/publishers")
    assert r_pubs.status_code == 200


def test_schema_dump_ignores_detached_when_configured():
    # Force JSON nested to ensure marshmallow attempts attribute access on relationships
    app = create_app(
        {
            "API_ADD_RELATIONS": True,
            "API_SERIALIZATION_TYPE": "json",
            # Safety net enabled by default, but set explicitly for clarity
            "API_SERIALIZATION_IGNORE_DETACHED": True,
        }
    )
    with app.app_context():
        # Fetch a book and then detach it from the session
        book = db.session.query(Book).first()
        assert book is not None

        # Build output schema (dump)
        _, schema = get_input_output_from_model_or_make(Book)

        # Detach/expunge to simulate detached instance during dump
        db.session.expunge(book)

        # Should not raise DetachedInstanceError; relations resolve to safe defaults
        with app.test_request_context("/api/books/1"):
            dumped = schema.dump(book)
        assert isinstance(dumped, dict)
        # Author field exists (json nested) but may be None when detached
        # Do not assert a value, just ensure no crash and key presence when configured
        assert "author" in dumped or "publisher" in dumped
