"""Tests for the ``API_FINAL_CALLBACK`` configuration option."""

from typing import Any

import pytest

from demo.basic_factory.basic_factory import create_app


# Simple callback used to mutate the response payload during tests.
def _final_callback(data: dict[str, Any]) -> dict[str, Any]:
    """Add a marker and mutate the title in the response payload."""
    data["callback_marker"] = True
    if isinstance(data.get("value"), dict):
        data["value"]["title"] = "Changed by callback"
    return data


@pytest.fixture
def client():
    app = create_app({"API_FINAL_CALLBACK": _final_callback})
    with app.app_context():
        yield app.test_client()


def test_final_callback_modifies_payload(client):
    """Ensure the final callback is invoked and mutates the response."""
    resp = client.get("/api/books/1")
    assert resp.status_code == 200
    assert resp.json["callback_marker"] is True
    assert resp.json["value"]["title"] == "Changed by callback"
