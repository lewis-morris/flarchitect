import pytest
from flask.testing import FlaskClient

from demo.basic_factory.basic_factory import create_app


@pytest.fixture
def client() -> FlaskClient:
    app = create_app({})
    return app.test_client()


def test_default_includes_fields(client):
    """By default ``response_ms`` and ``total_count`` are present."""
    resp = client.get("/api/books/1").json
    assert "response_ms" in resp
    assert "total_count" in resp


def test_disable_response_ms():
    app = create_app({"API_DUMP_RESPONSE_MS": False})
    client = app.test_client()
    resp = client.get("/api/books/1").json
    assert "response_ms" not in resp
    assert "total_count" in resp


def test_disable_total_count():
    app = create_app({"API_DUMP_TOTAL_COUNT": False})
    client = app.test_client()
    resp = client.get("/api/books/1").json
    assert "total_count" not in resp
    assert "response_ms" in resp
