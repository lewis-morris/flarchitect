from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

sys.modules.setdefault(
    "flarchitect.core.architect", types.SimpleNamespace(Architect=object)
)

from flarchitect.utils.session import get_session  # noqa: E402


def test_get_session_flask_sqlalchemy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session resolves automatically from Flask-SQLAlchemy."""
    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    db = SQLAlchemy()

    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)

    db.init_app(app)
    with app.app_context():
        closed = False

        def tracking_close() -> None:
            nonlocal closed
            closed = True
            db.session.remove()

        monkeypatch.setattr(db.session, "close", tracking_close)
        with get_session(User) as session:
            assert session is db.session
        assert closed


def test_get_session_plain_sqlalchemy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session derives from a model's bound engine without Flask."""

    class Base(DeclarativeBase):
        pass

    class Item(Base):
        __tablename__ = "items"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

    closed = False

    original_close = Session.close

    def tracking_close(self) -> None:  # noqa: D401 - simple wrapper
        nonlocal closed
        closed = True
        original_close(self)

    monkeypatch.setattr(Session, "close", tracking_close)

    with get_session(Item) as session:
        assert isinstance(session, Session)
    assert closed


def test_get_session_custom_getter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session resolves via configured callable."""

    engine = create_engine("sqlite:///:memory:")
    custom_session = Session(bind=engine)

    def custom_getter() -> Session:
        return custom_session

    monkeypatch.setattr(
        "flarchitect.utils.session.get_config_or_model_meta",
        lambda *_, **__: custom_getter,
    )
    closed = False

    original_close = custom_session.close

    def tracking_close() -> None:  # noqa: D401 - simple wrapper
        nonlocal closed
        closed = True
        original_close()

    monkeypatch.setattr(custom_session, "close", tracking_close)

    with get_session() as session:
        assert session is custom_session
    assert closed


def test_get_session_from_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session resolves from ``model.query.session`` attribute."""

    session_obj = object()

    class Model:
        query = SimpleNamespace(session=session_obj)

    monkeypatch.setattr(
        "flarchitect.utils.session.get_config_or_model_meta", lambda *_, **__: None
    )
    with get_session(Model) as session:
        assert session is session_obj


def test_get_session_legacy_method(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session resolves from model's legacy ``get_session`` method."""

    session_obj = object()

    class Model:
        @staticmethod
        def get_session() -> object:
            return session_obj

    monkeypatch.setattr(
        "flarchitect.utils.session.get_config_or_model_meta", lambda *_, **__: None
    )
    with get_session(Model) as session:
        assert session is session_obj


def test_get_session_model_metadata_bind(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session derives from ``model.metadata.bind`` when ``__table__`` is absent."""

    engine = create_engine("sqlite:///:memory:")

    class Model:
        metadata = SimpleNamespace(bind=engine)

    monkeypatch.setattr(
        "flarchitect.utils.session.get_config_or_model_meta", lambda *_, **__: None
    )
    closed = False

    original_close = Session.close

    def tracking_close(self) -> None:  # noqa: D401 - simple wrapper
        nonlocal closed
        closed = True
        original_close(self)

    monkeypatch.setattr(Session, "close", tracking_close)

    with get_session(Model) as session:
        assert isinstance(session, Session)
    assert closed


def test_get_session_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """An error is raised when no session strategy matches."""

    class Model:
        pass

    monkeypatch.setattr(
        "flarchitect.utils.session.get_config_or_model_meta", lambda *_, **__: None
    )
    with pytest.raises(RuntimeError), get_session(Model):
        pass
