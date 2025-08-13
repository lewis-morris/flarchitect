"""Demo application showcasing flarchitect field validators.

This package provides a minimal Flask application demonstrating how
:func:`flarchitect.schemas.validators.validate_by_type` integrates with
SQLAlchemy models.  It exposes :func:`create_app` which is used by the
unit tests and can be executed directly.
"""

from .app import User, create_app, db

__all__ = ["create_app", "db", "User"]
