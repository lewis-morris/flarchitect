"""Convenient exports for the :mod:`flarchitect` package.

This module exposes the primary public interface so users can simply do::

    from flarchitect import Architect

rather than importing from the internal ``core`` package.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _get_version

from .core.architect import Architect

try:
    __version__ = _get_version("flarchitect")
except PackageNotFoundError:  # pragma: no cover - fallback for editable installs
    __version__ = "0.0.0"

__all__ = ["Architect", "__version__"]
