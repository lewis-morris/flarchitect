"""Minimal Flask application illustrating field validators.

The application demonstrates how flarchitect's automatic field validation
works with SQLAlchemy models.  Each column defines validation rules via
the ``info`` mapping which ``flarchitect`` interprets to attach the
appropriate Marshmallow validators.
"""

from __future__ import annotations

from typing import Any

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect

# ``SQLAlchemy`` instance used by the demo app.  ``flarchitect`` will read
# models from this database when initialised inside :func:`create_app`.


class BaseModel(DeclarativeBase):
    """Base model providing a session accessor for flarchitect."""

    def get_session(*args: Any, **kwargs: Any):
        """Return the current database session."""

        return db.session


# create the SQLAlchemy extension using our BaseModel
db = SQLAlchemy(model_class=BaseModel)


class User(db.Model):
    """Simple user model with multiple validated fields.

    Attributes:
        id: Primary key for the user.
        email: User's email address. ``info={'validate': 'email'}`` triggers
            the built-in email validator which rejects invalid addresses.
        homepage: Personal website URL. ``info={'format': 'uri'}`` attaches a
            URL validator ensuring the string is a valid absolute URI.
        slug: Public identifier restricted to URL-friendly characters via the
            ``slug`` validator.
    """

    __tablename__ = "users"

    class Meta:
        """Expose the model through the API and group it under ``User``."""

        tag = "User"
        tag_group = "Demo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(
        String(120),
        info={"validate": "email"},  # Rejects values that are not emails
        nullable=False,
    )
    homepage: Mapped[str] = mapped_column(
        String(200),
        info={"format": "uri"},  # Adds URL validation automatically
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(50),
        info={"validate": "slug"},  # Ensures value is a URL-friendly slug
        nullable=False,
    )


def create_app(config: dict[str, Any] | None = None) -> Flask:
    """Build and configure the validator demo application.

    Args:
        config: Optional mapping to override default configuration values.

    Returns:
        A Flask application exposing REST endpoints for the :class:`User`
        model. Invalid field values raise ``ValidationError`` and return a
        ``400`` response.
    """

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        API_TITLE="Validator API",
        API_VERSION="1.0",
        API_BASE_MODEL=db.Model,
    )
    if config:
        app.config.update(config)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        # ``Architect`` scans the models and registers CRUD routes.
        Architect(app)

    return app


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    create_app().run(debug=True)
