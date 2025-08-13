from __future__ import annotations

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
