"""Tests for the caching demo application."""

from __future__ import annotations

import time

from flask.testing import FlaskClient

from demo.caching.app import app
from demo.model_extension.model.extensions import db
from demo.model_extension.model.models import Author


def test_author_endpoint_is_cached() -> None:
    """Responses are cached for the configured timeout."""
    client: FlaskClient = app.test_client()

    first = client.get("/api/authors/1").get_json()["value"]["first_name"]

    with app.app_context():
        author = db.session.get(Author, 1)
        author.first_name = "Cached"
        db.session.commit()

    second = client.get("/api/authors/1").get_json()["value"]["first_name"]
    assert second == first

    time.sleep(1.1)
    third = client.get("/api/authors/1").get_json()["value"]["first_name"]
    assert third == "Cached"
