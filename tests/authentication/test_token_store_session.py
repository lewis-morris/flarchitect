"""Tests ensuring token store sessions are properly closed."""

from __future__ import annotations

import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from flarchitect.authentication import token_store
from flarchitect.authentication.token_store import RefreshToken


class TrackingSession(Session):
    """Session subclass that records when it is closed."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.closed = False

    def close(self) -> None:  # type: ignore[override]
        self.closed = True
        super().close()


def _session_factory() -> tuple[sessionmaker, dict[str, TrackingSession]]:
    """Create an in-memory session factory and holder for tracking."""
    engine = create_engine("sqlite:///:memory:")
    factory = sessionmaker(bind=engine, class_=TrackingSession)
    holder: dict[str, TrackingSession] = {}
    return factory, holder


def test_store_refresh_token_closes_session(monkeypatch) -> None:
    """``store_refresh_token`` closes its database session."""
    factory, holder = _session_factory()

    def fake_get_session(model=None):  # pragma: no cover - runtime type
        holder["session"] = factory()
        return holder["session"]

    monkeypatch.setattr(token_store, "get_session", fake_get_session)
    token_store.store_refresh_token(
        "tok", "1", "carol", datetime.datetime.now(datetime.timezone.utc)
    )
    assert holder["session"].closed is True


def test_get_refresh_token_closes_session(monkeypatch) -> None:
    """``get_refresh_token`` closes its database session."""
    factory, holder = _session_factory()
    expires = datetime.datetime.now(datetime.timezone.utc)
    with factory() as session:
        token_store._ensure_table(session)
        session.add(
            RefreshToken(
                token="tok", user_pk="1", user_lookup="carol", expires_at=expires
            )
        )
        session.commit()

    def fake_get_session(model=None):  # pragma: no cover - runtime type
        holder["session"] = factory()
        return holder["session"]

    monkeypatch.setattr(token_store, "get_session", fake_get_session)
    assert token_store.get_refresh_token("tok") is not None
    assert holder["session"].closed is True


def test_delete_refresh_token_closes_session(monkeypatch) -> None:
    """``delete_refresh_token`` closes its database session."""
    factory, holder = _session_factory()
    expires = datetime.datetime.now(datetime.timezone.utc)
    with factory() as session:
        token_store._ensure_table(session)
        session.add(
            RefreshToken(
                token="tok", user_pk="1", user_lookup="carol", expires_at=expires
            )
        )
        session.commit()

    def fake_get_session(model=None):  # pragma: no cover - runtime type
        holder["session"] = factory()
        return holder["session"]

    monkeypatch.setattr(token_store, "get_session", fake_get_session)
    token_store.delete_refresh_token("tok")
    assert holder["session"].closed is True
