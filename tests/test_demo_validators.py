"""Tests for the validators demo application."""

from __future__ import annotations

import pytest
from flask.testing import FlaskClient

from demo.validators import create_app


@pytest.fixture()
def client() -> FlaskClient:
    """Provide a test client for the validator demo app."""

    app = create_app()
    with app.test_client() as client:
        yield client


def test_validation_errors(client: FlaskClient) -> None:
    """Invalid field data returns a 400 with error details."""

    response = client.post(
        "/api/users",
        json={"email": "not-email", "homepage": "not-url", "slug": "Bad Slug"},
    )
    assert response.status_code == 400
    data = response.get_json()
    error_fields = data["errors"]["error"]
    assert "email" in error_fields
    assert "homepage" in error_fields
    assert "slug" in error_fields
