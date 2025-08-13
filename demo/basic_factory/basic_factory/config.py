from demo.basic_factory.basic_factory.extensions import db


class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_BASE_MODEL = db.Model
    API_TITLE = "Book Shop API"
    API_VERSION = "0.1.0"
    API_VERBOSITY_LEVEL = 4
    SECRET_KEY = "8Kobns1_vnmg3rxnr0RZpkF4D1s"
    API_ALLOW_NESTED_WRITES = False
