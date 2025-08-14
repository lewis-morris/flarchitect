"""Integration test for the scaffolding demo with JWT auth."""

from __future__ import annotations

from demo.scaffolding import load
from demo.scaffolding.module.extensions import db
from demo.scaffolding.module.models import User


def test_scaffolding_jwt_auth() -> None:
    """Ensure the demo app generates JWT tokens and protects routes."""

    app = load()
    client = app.test_client()

    with app.app_context():
        db.drop_all()
        db.create_all()
        user = User(username="alice", email="alice@example.com")
        user.set_password("wonderland")
        db.session.add(user)
        db.session.commit()

    resp = client.post("/auth/login", json={"username": "alice", "password": "wonderland"})
    assert resp.status_code == 200
    tokens = resp.get_json()["value"]

    resp = client.get("/api/users", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert resp.status_code == 200
    data = resp.get_json()["value"]
    assert any(u["username"] == "alice" for u in data)
