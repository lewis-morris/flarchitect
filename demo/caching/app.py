"""Demo application showcasing response caching.

The app exposes a single ``Author`` model with a generated REST API. GET
responses are cached using the backend configured via ``API_CACHE_TYPE``.
``API_CACHE_TIMEOUT`` controls how long each cache entry lives. When the
``flask_caching`` package is installed the demo uses its ``Cache`` class; if
not, it falls back to :class:`flarchitect.core.simple_cache.SimpleCache`.
"""

from __future__ import annotations

import time
from typing import Any

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect


class BaseModel(DeclarativeBase):
    """Base model providing ``get_session`` for flarchitect."""

    def get_session(*args: Any) -> Any:  # type: ignore[no-untyped-def]
        return db.session


db = SQLAlchemy(model_class=BaseModel)


class Author(db.Model):
    """Simple author model used for demonstration."""

    __tablename__ = "author"

    class Meta:
        tag_group = "People/Companies"
        tag = "Author"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String)


def create_app(config: dict | None = None) -> Flask:
    """Application factory enabling response caching.

    The returned app caches GET responses. ``API_CACHE_TYPE`` selects the cache
    backend while ``API_CACHE_TIMEOUT`` defines the expiration in seconds.

    Args:
        config: Optional mapping to override default configuration.

    Returns:
        Configured :class:`~flask.Flask` instance.
    """

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        API_TITLE="Caching Demo",
        API_VERSION="1.0",
        API_BASE_MODEL=db.Model,
        API_CACHE_TYPE="SimpleCache",
        API_CACHE_TIMEOUT=1,
    )
    if config:
        app.config.update(config)

    db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.add(Author(first_name="Initial"))
        db.session.commit()

        architect = Architect(app)

        @app.route("/time")
        @architect.cache.cached()
        def current_time() -> dict[str, float]:
            """Return the current epoch time.

            The value is cached, so repeated calls within the timeout return
            the same response. After ``API_CACHE_TIMEOUT`` seconds, the cache is
            invalidated and a new timestamp is generated.
            """

            return {"time": time.time()}

    return app


if __name__ == "__main__":  # pragma: no cover - manual execution only
    create_app().run(debug=True)
