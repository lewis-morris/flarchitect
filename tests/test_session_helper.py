from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from flarchitect.utils.session import get_session


def test_get_session_flask_sqlalchemy() -> None:
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
        assert get_session(User) is db.session


def test_get_session_plain_sqlalchemy() -> None:
    """Session derives from a model's bound engine without Flask."""

    class Base(DeclarativeBase):
        pass

    class Item(Base):
        __tablename__ = "items"
        id: Mapped[int] = mapped_column(Integer, primary_key=True)

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)

    session = get_session(Item)
    try:
        assert isinstance(session, Session)
    finally:
        session.close()


def test_get_session_custom_getter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session resolves via configured callable."""

    engine = create_engine("sqlite:///:memory:")
    custom_session = Session(bind=engine)

    def custom_getter() -> Session:
        return custom_session

    monkeypatch.setattr("flarchitect.utils.session.get_config_or_model_meta", lambda *_, **__: custom_getter)
    try:
        assert get_session() is custom_session
    finally:
        custom_session.close()


def test_get_session_from_query(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session resolves from ``model.query.session`` attribute."""

    session_obj = object()

    class Model:
        query = SimpleNamespace(session=session_obj)

    monkeypatch.setattr("flarchitect.utils.session.get_config_or_model_meta", lambda *_, **__: None)
    assert get_session(Model) is session_obj


def test_get_session_legacy_method(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session resolves from model's legacy ``get_session`` method."""

    session_obj = object()

    class Model:
        @staticmethod
        def get_session() -> object:
            return session_obj

    monkeypatch.setattr("flarchitect.utils.session.get_config_or_model_meta", lambda *_, **__: None)
    assert get_session(Model) is session_obj


def test_get_session_model_metadata_bind(monkeypatch: pytest.MonkeyPatch) -> None:
    """Session derives from ``model.metadata.bind`` when ``__table__`` is absent."""

    engine = create_engine("sqlite:///:memory:")

    class Model:
        metadata = SimpleNamespace(bind=engine)

    monkeypatch.setattr("flarchitect.utils.session.get_config_or_model_meta", lambda *_, **__: None)
    session = get_session(Model)
    try:
        assert isinstance(session, Session)
    finally:
        session.close()


def test_get_session_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """An error is raised when no session strategy matches."""

    class Model:
        pass

    monkeypatch.setattr("flarchitect.utils.session.get_config_or_model_meta", lambda *_, **__: None)
    with pytest.raises(RuntimeError):
        get_session(Model)
