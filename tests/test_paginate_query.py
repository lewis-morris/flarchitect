from typing import Any

import pytest

from demo.basic_factory.basic_factory import create_app
from demo.basic_factory.basic_factory.extensions import db
from demo.basic_factory.basic_factory.models import Book
from flarchitect.database.operations import CrudService, paginate_query


@pytest.fixture
def app():
    """Create a demo application for testing."""
    return create_app()


def test_paginate_query_returns_paginated_query_and_default(app):
    """Paginate a query and return default pagination size."""
    with app.app_context():
        query = db.session.query(Book)
        paginated, default_size = paginate_query(query, page=1, items_per_page=1)
        assert len(paginated.items) == 1
        assert default_size == 20


def test_crud_service_uses_single_count_for_pagination(app, monkeypatch):
    """Ensure CrudService does not trigger an extra count during pagination."""

    with app.app_context(), app.test_request_context("/books?page=1&limit=1"):
        service = CrudService(Book, db.session)

        count_calls: dict[str, int] = {"value": 0}
        captured_kwargs: dict[str, Any] = {}
        query_class = type(db.session.query(Book))

        def fake_count(self):  # pragma: no cover - used for behavioural assertion only
            count_calls["value"] += 1
            return 7

        class DummyPagination:
            def __init__(self) -> None:
                self.items = ["sentinel"]

            def all(self) -> list[str]:
                return self.items

        def fake_paginate(
            self,
            page=None,
            per_page=None,
            error_out=None,
            count=True,
            **kwargs,
        ):  # pragma: no cover - patched for assertions
            captured_kwargs.update({"page": page, "per_page": per_page, "error_out": error_out, **kwargs})
            captured_kwargs.setdefault("count", count)
            return DummyPagination()

        monkeypatch.setattr(query_class, "count", fake_count, raising=False)
        monkeypatch.setattr(query_class, "paginate", fake_paginate, raising=False)

        result = service.get_query({"page": 1, "limit": 1})

        assert count_calls["value"] == 1
        assert captured_kwargs.get("count") is False
        assert result["total_count"] == 7
