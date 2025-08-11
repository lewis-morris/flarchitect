"""Demo application showing configuration precedence in flarchitect.

This example demonstrates how global and model-specific configuration
values interact. Run the application and inspect the generated API to see
rate limits applied at different levels.
"""
from __future__ import annotations

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect.core.architect import Architect


class BaseModel(DeclarativeBase):
    """SQLAlchemy base model used by the demo."""

    def get_session(*args) -> SQLAlchemy.Session:  # type: ignore[name-defined]
        """Return the SQLAlchemy session for the current app context."""
        return db.session  # type: ignore[name-defined]


app = Flask(__name__)

db = SQLAlchemy(model_class=BaseModel)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
app.config["API_TITLE"] = "Config Demo API"
app.config["API_VERSION"] = "1.0"
app.config["API_BASE_MODEL"] = db.Model
app.config["API_RATE_LIMIT"] = "100 per minute"
app.config["API_GET_RATE_LIMIT"] = "50 per minute"


class Author(db.Model):
    """Simple model with overriding rate limit configuration."""

    __tablename__ = "author"

    class Meta:  # noqa: D106 - simple configuration container
        tag_group = "People/Companies"
        tag = "Author"
        rate_limit = "10 per minute"
        get_rate_limit = "5 per minute"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)


with app.app_context():
    db.init_app(app)
    db.create_all()
    Architect(app)


if __name__ == "__main__":
    app.run(debug=True)
