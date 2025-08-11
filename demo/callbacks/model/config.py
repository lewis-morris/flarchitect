from demo.callbacks.model.callbacks import (
    dump_callback,
    error_callback,
    final_callback,
    return_callback,
    setup_callback,
)
from demo.callbacks.model.extensions import db


class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_BASE_MODEL = db.Model
    API_TITLE = "Book Shop API"
    API_VERSION = "0.1.0"
    API_VERBOSITY_LEVEL = 4
    API_DOCS_FONT = "montserrat"
    API_RATE_LIMIT = "5 per minute"
    SECRET_KEY = "8Kobns1_vnmg3rxnr0RZpkF4D1s"
    API_SETUP_CALLBACK = setup_callback
    API_RETURN_CALLBACK = return_callback
    API_FINAL_CALLBACK = final_callback
    API_ERROR_CALLBACK = error_callback
    API_DUMP_CALLBACK = dump_callback
