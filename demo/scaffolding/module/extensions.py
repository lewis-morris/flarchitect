"""Extension instances for the scaffolding application."""

from flask_sqlalchemy import SQLAlchemy

from flarchitect import Architect

# Instantiate extensions globally to be initialized in the app factory.
db = SQLAlchemy()
schema = Architect()

__all__ = ["db", "schema"]
