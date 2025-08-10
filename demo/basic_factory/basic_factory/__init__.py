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
        from demo.basic_factory.basic_factory.models import (
            Author,
            Book,
            Category,
            Publisher,
            Review,
        )

        db.create_all()
        load_dummy_database(db)
        schema.init_app(app)

    return app
