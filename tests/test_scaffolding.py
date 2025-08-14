"""Tests for the scaffolding example."""

from __future__ import annotations

import pytest

from demo.scaffolding import load
from demo.scaffolding.module.extensions import db
from demo.scaffolding import User


@pytest.fixture()
def app():
    app = load("Scaffolding.config.TestingConfig")
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


def test_register_login_and_protected(client):
    response = client.post(
        "/register",
        json={"username": "tester", "email": "tester@example.com", "password": "secret"},
    )
    assert response.status_code == 201

    response = client.post("/login", json={"username": "tester", "password": "secret"})
    assert response.status_code == 200
    token = response.get_json()["access_token"]

    response = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.get_json()["user_id"] == 1


def test_username_validation(app):
    with app.app_context(), pytest.raises(ValueError):
        user = User(username="ab", email="a@example.com")
        user.set_password("secret")
        db.session.add(user)
        db.session.commit()
