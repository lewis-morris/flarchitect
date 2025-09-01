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


def test_request_id_not_in_body_by_default():
    """By default, request_id is only returned via header, not body."""
    app = create_app({})
    client = app.test_client()
    r = client.get("/api/books/1")
    body = r.get_json()
    assert "request_id" not in body
    # But header should be present
    assert r.headers.get("X-Request-ID")


def test_request_id_in_body_when_enabled():
    """request_id appears in body when API_DUMP_REQUEST_ID=True."""
    app = create_app({"API_DUMP_REQUEST_ID": True})
    client = app.test_client()
    r = client.get("/api/books/1")
    body = r.get_json()
    rid_header = r.headers.get("X-Request-ID")
    assert "request_id" in body
    assert isinstance(body["request_id"], str)
    # Value should match header correlation id
    assert body["request_id"] == rid_header
