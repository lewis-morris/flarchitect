"""Demo application showcasing Cross-Origin Resource Sharing (CORS).

The application exposes a single ``/ping`` route. When ``API_ENABLE_CORS`` is
set to ``True`` the response includes the ``Access-Control-Allow-Origin``
header, allowing browsers to call the API from other origins.
"""

from __future__ import annotations

from typing import Any

from flask import Flask

from flarchitect import Architect


def create_app(config: dict[str, Any] | None = None) -> Flask:
    """Application factory enabling CORS support.

    Args:
        config: Optional mapping to override default configuration.

    Returns:
        Configured :class:`~flask.Flask` instance.
    """

    app = Flask(__name__)
    app.config.update(
        API_ENABLE_CORS=True,
        CORS_RESOURCES={r"/ping": {"origins": "*"}},
        FULL_AUTO=False,
        API_CREATE_DOCS=False,
    )
    if config:
        app.config.update(config)

    with app.app_context():
        Architect(app)

    @app.get("/ping")
    def ping() -> str:
        """Return a simple pong message."""

        return "pong"

    return app


if __name__ == "__main__":  # pragma: no cover - manual execution only
    create_app().run(debug=True)
