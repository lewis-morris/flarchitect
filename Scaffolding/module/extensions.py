"""Extension instances for the scaffolding application."""

from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

# Instantiate extensions globally to be initialized in the app factory.
db = SQLAlchemy()
jwt = JWTManager()

__all__ = ["db", "jwt"]
