"""Demo API showcasing custom field name casing."""

from __future__ import annotations

from typing import Any

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect


class BaseModel(DeclarativeBase):
    """Base model providing a session accessor for flarchitect."""

    def get_session(*args: Any, **kwargs: Any) -> Any:
        """Return the current database session."""

        return db.session


# SQLAlchemy instance using the custom base model above.
db = SQLAlchemy(model_class=BaseModel)


class Person(db.Model):
    """Simple person model used in the field case demo."""

    __tablename__ = "people"

    class Meta:
        """Expose the model through the API and group it under ``Person``."""

        tag = "Person"
        tag_group = "Demo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(80), nullable=False)
    last_name: Mapped[str] = mapped_column(String(80), nullable=False)


def create_app(config: dict[str, Any] | None = None) -> Flask:
    """Build and configure the field casing demo application.

    Args:
        config: Optional mapping to override default configuration values.

    Returns:
        Configured Flask application exposing camelCased fields.
    """

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        API_TITLE="Field Casing API",
        API_VERSION="1.0",
        API_BASE_MODEL=db.Model,
        API_FIELD_CASE="camel",
    )
    if config:
        app.config.update(config)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        Architect(app)

    return app


if __name__ == "__main__":  # pragma: no cover - manual execution helper
    create_app().run(debug=True)
