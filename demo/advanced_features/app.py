"""Advanced demo showcasing multiple flarchitect features.

This example combines soft deletes, nested writes, validation, custom
callbacks and per HTTP-method configuration.  Run this file directly and use
the ``curl`` commands in the repository ``README`` to exercise the API.
"""

from __future__ import annotations

import datetime
from typing import Any

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from flarchitect import Architect


class BaseModel(DeclarativeBase):
    """Base model with timestamp and soft delete columns."""

    # ``created`` and ``updated`` are automatically managed timestamps.
    created: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    # ``deleted`` enables soft deletes when ``API_SOFT_DELETE`` is set.
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def get_session(*args: Any, **kwargs: Any):  # noqa: D401 - simple passthrough
        """Return the current database session."""

        return db.session


# Global SQLAlchemy instance using the custom base model above.
db = SQLAlchemy(model_class=BaseModel)


class Author(db.Model):
    """Author of one or more books."""

    __tablename__ = "author"

    class Meta:
        # ``tag`` and ``tag_group`` drive grouping in the generated documentation.
        tag = "Author"
        tag_group = "People"
        # Restrict HTTP methods to ``GET`` and ``POST`` only.
        allowed_methods = ["GET", "POST"]
        # Apply a rate limit specifically to author creation.
        post_rate_limit = "5 per minute"
        # Provide custom descriptions for documentation per HTTP method.
        description = {
            "GET": "Retrieve authors, optionally including soft-deleted records.",
            "POST": "Create a new author record.",
        }

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Author's name – simple string field.
    name: Mapped[str] = mapped_column(String(80))
    # Optional contact email with validation and helpful docs metadata.
    email: Mapped[str | None] = mapped_column(
        String(120),
        info={
            "description": "Author's contact email.",
            "format": "email",
            "validator": "email",
            "validator_message": "Invalid email address.",
        },
    )
    # Optional website; ``format`` automatically enables URL validation.
    website: Mapped[str | None] = mapped_column(
        String(255),
        info={"description": "Author website", "format": "uri"},
    )
    # Back-reference of books written by this author.
    books: Mapped[list[Book]] = relationship(back_populates="author")


class Book(db.Model):
    """Book written by an author."""

    __tablename__ = "book"

    class Meta:
        tag = "Book"
        tag_group = "Content"
        # Allow nested writes so books can be created alongside their author.
        allow_nested_writes = True
        # Capitalise titles before saving using ``_add_callback`` below.
        add_callback = staticmethod(lambda obj, model: _add_callback(obj))
        # Provide custom descriptions for generated documentation.
        description = {
            "GET": "Retrieve books with their associated authors.",
            "POST": "Create a book and, optionally, its author in one request.",
            "PATCH": "Update a book's details.",
        }
        # Demonstrate HTTP method specific configuration.
        patch_rate_limit = "10 per minute"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # The book's title.
    title: Mapped[str] = mapped_column(String(120))
    # Foreign key relationship to ``Author``.
    # ``author_id`` is optional to support nested author creation.
    author_id: Mapped[int | None] = mapped_column(ForeignKey("author.id"), nullable=True)
    author: Mapped[Author] = relationship(back_populates="books")


def _add_callback(obj: Book) -> Book:
    """Ensure book titles are capitalised before saving."""

    obj.title = obj.title.title()
    return obj


def dump_callback(data: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Attach a debug flag to every serialised response."""

    data["debug"] = True
    return data


def create_app() -> Flask:
    """Build the Flask application and initialise flarchitect.

    Returns:
        Configured Flask application.
    """

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        API_TITLE="Advanced API",
        API_VERSION="1.0",
        API_BASE_MODEL=db.Model,
        API_ALLOW_NESTED_WRITES=True,
        API_SOFT_DELETE=True,
        API_SOFT_DELETE_ATTRIBUTE="deleted",
        API_SOFT_DELETE_VALUES=(False, True),
        API_DUMP_CALLBACK=dump_callback,
    )

    db.init_app(app)
    with app.app_context():
        db.create_all()
        Architect(app)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
