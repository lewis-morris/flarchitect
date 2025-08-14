"""Configuration module for the scaffolding application."""

from __future__ import annotations

import os

from .extensions import db
from .models import User


class Config:
    """Base configuration with sensible defaults.

    Environment variables may override these values. Each option lists
    possible values and defaults for clarity.
    """

    # Flask settings
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///:memory:")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.getenv("DEBUG", False)

    # flarchitect configuration
    API_BASE_MODEL = db.Model
    API_TITLE = "Scaffolding API"
    API_VERSION = "0.1.0"
    API_VERBOSITY_LEVEL = 4
    API_ALLOW_NESTED_WRITES = True
    API_CREATE_DOCS = True
    API_ENABLE_CORS = False
    API_DOCUMENTATION_PASSWORD = os.getenv("API_DOCUMENTATION_PASSWORD")
    API_DOCUMENTATION_REQUIRE_AUTH = False
    API_SOFT_DELETE = True
    API_SOFT_DELETE_ATTRIBUTE = "deleted"
    API_SOFT_DELETE_VALUES = (False, True)

    # Authentication configuration
    API_AUTHENTICATE = True
    API_AUTHENTICATE_METHOD = ["jwt"]
    API_USER_MODEL = User
    API_USER_LOOKUP_FIELD = "username"
    API_CREDENTIAL_CHECK_METHOD = "check_password"
    ACCESS_SECRET_KEY = os.getenv("ACCESS_SECRET_KEY", "access-secret")
    REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY", "refresh-secret")
    API_JWT_EXPIRY_TIME = 15
    API_JWT_REFRESH_EXPIRY_TIME = 1440
    API_DOCS_STYLE = "redoc"
    # Demo-specific options
    USERNAME_MIN_LENGTH = 3


class TestingConfig(Config):
    """Configuration used during unit tests."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    API_JWT_EXPIRY_TIME = 1
    API_JWT_REFRESH_EXPIRY_TIME = 2
