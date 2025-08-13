"""Tests for the validators demo application."""

from __future__ import annotations

from flask.testing import FlaskClient

from demo.validators.app import app

VALID_PAYLOAD = {
    "name": "Test Publisher",
    "website": "https://example.com",
    "email": "publisher@example.com",
    "foundation_year": 1999,
}


def test_author_email_validation() -> None:
    """Valid data succeeds while invalid email triggers a 400 response."""
    client: FlaskClient = app.test_client()

    good = client.post("/api/publishers", json=VALID_PAYLOAD)
    assert good.status_code == 200
    assert good.get_json()["value"]["email"] == VALID_PAYLOAD["email"]

    bad_payload = dict(VALID_PAYLOAD)
    bad_payload["email"] = "not-an-email"
    bad = client.post("/api/publishers", json=bad_payload)
    assert bad.status_code == 400
