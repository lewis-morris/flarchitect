"""Application factory for the scaffolding example."""

from flask import Flask

from .extensions import db, jwt
from .routes import api_bp


def create_app(config_class: str) -> Flask:
    """Application factory.

    Args:
        config_class: Dotted path to the configuration object.

    Returns:
        Configured :class:`flask.Flask` application.
    """

    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(api_bp)

    with app.app_context():
        db.create_all()

    return app
