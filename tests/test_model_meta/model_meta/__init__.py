from flask import Flask

from demo.model_extension.helpers import load_dummy_database
from demo.model_extension.model.config import Config
from demo.model_extension.model.extensions import db, schema


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
        db.create_all()
        load_dummy_database(db)
        schema.init_app(app)

    return app
