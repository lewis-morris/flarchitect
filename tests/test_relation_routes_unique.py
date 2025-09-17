from __future__ import annotations

from typing import Any

from flask import Flask
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship

from flarchitect.core.architect import Architect


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    class Meta:
        tag_group = "Test"
        tag = "Users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)


class Friend(Base):
    __tablename__ = "friends"

    class Meta:
        tag_group = "Test"
        tag = "Friends"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    friend_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))

    # Two relationships to the same target model with distinct keys
    user: Mapped[User] = relationship(User, foreign_keys=[user_id])
    friend: Mapped[User] = relationship(User, foreign_keys=[friend_id])


def _make_app(naming: str = "relationship") -> tuple[Flask, Session]:
    app = Flask(__name__)
    app.config.update(
        {
            "TESTING": True,
            "FULL_AUTO": True,
            "API_BASE_MODEL": Base,
            # Ensure relations are generated and use the chosen style
            "API_ADD_RELATIONS": True,
            "API_RELATION_ROUTE_NAMING": naming,
            # Trim overhead in tests
            "API_CREATE_DOCS": True,
        }
    )

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

    # Seed data
    from sqlalchemy.orm import sessionmaker

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    u1 = User(name="Alice")
    u2 = User(name="Bob")
    session.add_all([u1, u2])
    session.flush()
    f = Friend(user_id=u1.id, friend_id=u2.id)
    session.add(f)
    session.commit()

    # Initialise within app context for config/meta resolution
    with app.app_context():
        Architect(app)  # auto-initialises and registers routes/spec
    return app, session


def test_relation_routes_use_relation_key_segment() -> None:
    app, _ = _make_app(naming="relationship")
    client = app.test_client()

    # Expect distinct endpoints per relation key to be registered
    rules = {r.rule for r in app.url_map.iter_rules()}
    assert "/api/friends/<int:id>/user" in rules
    assert "/api/friends/<int:id>/friend" in rules

    # OpenAPI should include both relation endpoints
    spec = client.get("/docs/apispec.json").get_json()
    paths: dict[str, Any] = spec.get("paths", {})
    assert any(p.endswith("/friends/{id}/user") for p in paths)
    assert any(p.endswith("/friends/{id}/friend") for p in paths)


def test_relation_routes_target_model_style_backcompat() -> None:
    app, _ = _make_app(naming="model")
    client = app.test_client()

    # Old behaviour uses target model endpoint as final segment
    rules = {r.rule for r in app.url_map.iter_rules()}
    assert "/api/friends/<int:id>/users" in rules

    # Ensure docs JSON available
    spec_resp = client.get("/docs/apispec.json")
    assert spec_resp.status_code == 200
