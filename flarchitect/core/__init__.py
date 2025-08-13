"""Core routing utilities and caching primitives.

This package exposes the main classes used to build and register API
endpoints as well as a lightweight in-memory cache for environments where
``flask_caching`` is unavailable.
"""

from .architect import Architect, jwt_authentication
from .routes import RouteCreator, find_rule_by_function
from .simple_cache import SimpleCache

__all__ = [
    "Architect",
    "jwt_authentication",
    "RouteCreator",
    "find_rule_by_function",
    "SimpleCache",
]
