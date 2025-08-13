import pytest

from demo.basic_factory.basic_factory import create_app
from demo.basic_factory.basic_factory.extensions import db
from demo.basic_factory.basic_factory.models import Book
from flarchitect.database.operations import paginate_query


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
