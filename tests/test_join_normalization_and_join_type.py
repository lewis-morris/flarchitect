import pytest

from demo.basic_factory.basic_factory import create_app
from demo.basic_factory.basic_factory.extensions import db
from demo.basic_factory.basic_factory.models import Book
from flarchitect.database.utils import get_models_for_join
from flarchitect.database.operations import CrudService


@pytest.fixture
def app():
    app = create_app(
        {
            "API_ALLOW_JOIN": True,
            "API_ADD_RELATIONS": True,
            "API_SERIALIZATION_TYPE": "url",  # explicit default for override test
        }
    )
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_get_models_for_join_normalises_tokens_and_pluralisation(app):
    with app.app_context():
        service = CrudService(Book, db.session)
        # Mix plural and singular forms; include whitespace noise
        args = {"join": " authors, publisher , reviews"}
        models = get_models_for_join(args, service.fetch_related_model_by_name)
        # We expect Author, Publisher, Review models to be resolved (order independent)
        resolved = {m.__name__ for m in models.values()}
        assert {"Author", "Publisher", "Review"}.issubset(resolved)


def test_dump_override_enables_dynamic_when_config_is_url(client):
    # Default serialization is URL; override to dynamic per request
    resp = client.get("/api/books?dump=dynamic&join=author,publisher&limit=1").get_json()
    assert resp["status_code"] == 200
    book = resp["value"][0]
    assert isinstance(book.get("author"), dict)
    assert isinstance(book.get("publisher"), dict)


def test_join_type_left_includes_all_base_rows(client):
    # Base count of publishers
    base = client.get("/api/publishers?limit=1").get_json()
    base_total = base["total_count"]

    # Inner join: only publishers with books
    inner = client.get("/api/publishers?join=books&join_type=inner").get_json()
    inner_total = inner["total_count"]

    # Left join: should be >= inner and equal to base
    left = client.get("/api/publishers?join=books&join_type=left").get_json()
    left_total = left["total_count"]

    assert left_total >= inner_total
    assert left_total == base_total

