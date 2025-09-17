from __future__ import annotations

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

    user: Mapped[User] = relationship(User, foreign_keys=[user_id])
    friend: Mapped[User] = relationship(User, foreign_keys=[friend_id])


def _mk_app(naming: str | None = None, meta_override: bool = False, alias_map: dict[str, str] | None = None, meta_override_name: str | None = None) -> Flask:
    app = Flask(__name__)
    cfg = {
        "TESTING": True,
        "FULL_AUTO": True,
        "API_BASE_MODEL": Base,
        "API_ADD_RELATIONS": True,
        "API_CREATE_DOCS": True,
    }
    if naming:
        cfg["API_RELATION_ROUTE_NAMING"] = naming
    app.config.update(cfg)

    # Reset any previous overrides for isolation between tests
    if hasattr(Friend.Meta, "relation_route_naming"):
        delattr(Friend.Meta, "relation_route_naming")
    if hasattr(Friend.Meta, "relation_route_map"):
        delattr(Friend.Meta, "relation_route_map")

    if meta_override:
        # Inject per-model Meta override for naming strategy
        Friend.Meta.relation_route_naming = meta_override_name or naming
    if alias_map is not None:
        Friend.Meta.relation_route_map = alias_map

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

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

    with app.app_context():
        Architect(app)
    return app


def _rules(app: Flask) -> set[str]:
    return {r.rule for r in app.url_map.iter_rules()}


def _endpoints(app: Flask) -> set[str]:
    return {r.endpoint for r in app.url_map.iter_rules()}


def test_naming_model_default_routes():
    app = _mk_app(naming="model")
    rules = _rules(app)
    assert "/api/friends/<int:id>/users" in rules


def test_naming_relationship_routes():
    app = _mk_app(naming="relationship")
    rules = _rules(app)
    assert "/api/friends/<int:id>/user" in rules
    assert "/api/friends/<int:id>/friend" in rules
    # Idempotency: function names include suffix only once
    eps = [e for e in _endpoints(app) if "friends" in e]
    assert any(e.endswith("_user") for e in eps)
    assert any(e.endswith("_friend") for e in eps)
    assert not any(e.endswith("_user_user") for e in eps)


def test_naming_auto_switches_to_relationship_on_collision():
    app = _mk_app(naming="auto")
    rules = _rules(app)
    # Should resolve to relationship keys for multi-FK
    assert "/api/friends/<int:id>/user" in rules
    assert "/api/friends/<int:id>/friend" in rules


def test_per_model_override_takes_precedence():
    # Even with global model naming, per-model override to relationship should win
    app = _mk_app(naming="model", meta_override=True, meta_override_name="relationship")
    rules = _rules(app)
    assert "/api/friends/<int:id>/user" in rules
    assert "/api/friends/<int:id>/friend" in rules


def test_alias_map_applies_to_url_segment_only_when_relationship_based():
    app = _mk_app(naming="relationship", alias_map={"user": "owner", "friend": "contact"})
    rules = _rules(app)
    assert "/api/friends/<int:id>/owner" in rules
    assert "/api/friends/<int:id>/contact" in rules
