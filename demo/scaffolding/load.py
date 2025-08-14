"""Application loader for the scaffolding example."""

from __future__ import annotations

from typing import TYPE_CHECKING

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


if __name__ == "__main__":
    flask_app = load()
    flask_app.run(host="0.0.0.0", port=5000, debug=True)
