"""Application loader for the scaffolding example."""

from __future__ import annotations

from typing import TYPE_CHECKING

from werkzeug.serving import run_simple

from flarchitect.logging import logger

try:  # pragma: no cover - prefer package import
    from .module import create_app
except ImportError:  # pragma: no cover - direct script execution
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parent))
    from module import create_app  # type: ignore

if TYPE_CHECKING:  # pragma: no cover
    from flask import Flask


def load() -> Flask:
    """Return a configured :class:`~flask.Flask` app for the demo."""

    return create_app()


def app_factory() -> Flask:
    """Create the demo application and log the documentation URL.

    Returns:
        Flask: The configured Flask application.
    """
    app = load()
    docs_url = app.config.get("API_DOCUMENTATION_URL", "/docs")
    logger.log(1, f"|Documentation available at| `http://localhost:5000{docs_url}`")
    return app


if __name__ == "__main__":
    run_simple("0.0.0.0", 5000, app_factory, use_reloader=True, use_debugger=True)
