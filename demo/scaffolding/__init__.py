"""Scaffolding package exposing the load helper and models."""

from .load import load
from .module.models import User

__all__ = ["load", "User"]
