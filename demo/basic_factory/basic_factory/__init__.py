from flask import Flask

from demo.basic_factory.basic_factory.config import Config
from demo.basic_factory.basic_factory.extensions import db, schema
from demo.utils.helpers import load_dummy_database


def create_app(config: dict = None):
    """
    Creates the flask app.
    Args:
        config (Optional[dict]): The configuration dictionary.

    Returns:

    """
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    db.init_app(app)

    with app.app_context():
        # Import models for their side effects so SQLAlchemy can register them
        import demo.basic_factory.basic_factory.models  # noqa: F401

        db.create_all()
        load_dummy_database(db)
        schema.init_app(app)

    return app
