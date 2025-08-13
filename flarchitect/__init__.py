"""Convenient exports for the :mod:`flarchitect` package.

This module exposes the primary public interface so users can simply do::

    from flarchitect import Architect

rather than importing from the internal ``core`` package.
"""

from .core.architect import Architect

__all__ = ["Architect"]
