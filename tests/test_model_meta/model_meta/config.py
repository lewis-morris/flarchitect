from demo.model_extension.model.extensions import db


class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_BASE_MODEL = db.Model
    API_TITLE = "Book Shop API"
    API_VERSION = "0.1.0"
    API_VERBOSITY_LEVEL = 4
    API_DOCS_FONT = "jetbrains_mono"
    API_RATE_LIMIT = "5 per minute"
    SECRET_KEY = "8Kobns1_vnmg3rxnr0RZpkF4D1s"
