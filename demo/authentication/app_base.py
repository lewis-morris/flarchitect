"""Common application setup used across authentication demos."""

from __future__ import annotations

from dataclasses import dataclass

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect


class BaseModel(DeclarativeBase):
    """Base SQLAlchemy model with a :func:`get_session` helper."""

    def get_session(*args):  # type: ignore[no-untyped-def]
        """Return the active database session."""
        return db.session


db = SQLAlchemy(model_class=BaseModel)
schema = Architect()


class User(db.Model):
    """Very small user model for authentication examples."""

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()
    api_key: Mapped[str | None] = mapped_column(nullable=True)
    roles: Mapped[list[str]] = mapped_column(JSON, default=list)

    def check_password(self, candidate: str) -> bool:
        """Compare stored password with ``candidate``.

        Password hashing is intentionally omitted to keep the example focused on
        authentication wiring rather than security implementation details.
        """

        return self.password == candidate


@dataclass
class BaseConfig:
    """Base configuration shared by all authentication examples."""

    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    API_BASE_MODEL = db.Model
    API_TITLE: str = "Book Shop API"
    API_VERSION: str = "0.1.0"
    API_VERBOSITY_LEVEL: int = 4
    SECRET_KEY: str = "change-me"


def create_app(config: type[BaseConfig]) -> Flask:
    """Application factory used by the example modules."""

    app = Flask(__name__)
    app.config.from_object(config)

    with app.app_context():
        db.init_app(app)
        schema.init_app(app)
    return app
