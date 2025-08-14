"""Application factory for the scaffolding example."""

from flask import Flask

from .config import Config
from .extensions import db, schema


def create_app() -> Flask:
    """Application factory.

    Args:
        config_class: Dotted path to the configuration object.

    Returns:
        Configured :class:`flask.Flask` application.
    """

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        # Import models for their side effects so SQLAlchemy registers them
        from . import models  # noqa: F401

        db.create_all()
        schema.init_app(app)

    return app
