"""Configuration module for the scaffolding application."""

from __future__ import annotations

import os
from datetime import timedelta


class Config:
    """Base configuration with sensible defaults.

    Environment variables may override these values. Each option lists
    possible values and defaults for clarity.
    """

    SECRET_KEY = os.getenv("SECRET_KEY", "dev")  # str: secret for session and JWT; default "dev"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///:memory:")  # str: any SQLAlchemy-supported URI; default in-memory SQLite
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # bool: enable change tracking; default False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")  # str: secret used to sign JWTs; default "dev-jwt-secret"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)  # timedelta: token lifetime; default 15 minutes
    JWT_TOKEN_LOCATION = ["headers"]  # list[str]: where to read JWTs ("headers", "cookies", "json"); default ["headers"]
    DEBUG = os.getenv("DEBUG", False)  # bool: enable debug mode; default False
    USERNAME_MIN_LENGTH = 3  # int: minimum username length; default 3


class TestingConfig(Config):
    """Configuration used during unit tests."""

    TESTING = True  # bool: put Flask in testing mode
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # use in-memory DB for tests
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=1)  # shorter token lifetime for tests
