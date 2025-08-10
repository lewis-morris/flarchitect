from demo.soft_delete.soft_delete.extensions import db


class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    API_BASE_MODEL = db.Model
    API_TITLE = "Book Shop API"
    API_VERSION = "0.1.0"
    API_VERBOSITY_LEVEL = 4
    API_SOFT_DELETE = True
    API_SOFT_DELETE_ATTRIBUTE = "deleted"
    API_SOFT_DELETE_VALUES = (False, True)

    SECRET_KEY = "8Kobns1_vnmg3rxnr0RZpkF4D1s"
