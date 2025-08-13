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

    created: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def get_session(*args: Any, **kwargs: Any):
        """Return the current database session."""

        return db.session


db = SQLAlchemy(model_class=BaseModel)


class Author(db.Model):
    """Author of one or more books."""

    __tablename__ = "author"

    class Meta:
        tag = "Author"
        tag_group = "People"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    books: Mapped[list[Book]] = relationship(back_populates="author")


class Book(db.Model):
    """Book written by an author."""

    __tablename__ = "book"

    class Meta:
        tag = "Book"
        tag_group = "Content"
        allow_nested_writes = True
        add_callback = staticmethod(lambda obj, model: _add_callback(obj))

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(back_populates="books")


def _add_callback(obj: Book) -> Book:
    """Ensure book titles are capitalised before saving."""

    obj.title = obj.title.title()
    return obj


def return_callback(model: type[BaseModel], output: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """Attach a debug flag to every response.

    Args:
        model: Model class being processed.
        output: Response payload.

    Returns:
        Modified response dictionary.
    """

    output["debug"] = True
    return {"output": output}


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
        API_RETURN_CALLBACK=return_callback,
    )

    db.init_app(app)
    with app.app_context():
        db.create_all()
        Architect(app)

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
