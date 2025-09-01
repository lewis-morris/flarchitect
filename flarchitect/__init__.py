"""Convenient exports for the :mod:`flarchitect` package.

This module exposes the primary public interface so users can simply do::

    from flarchitect import Architect

rather than importing from the internal ``core`` package.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _get_version

import werkzeug

from . import authentication as authentication  # expose subpackage for monkeypatch
from . import core as core  # makes "flarchitect.core" available as attribute
from . import logging as logging  # expose module for monkeypatch
from . import utils as utils  # expose subpackage for monkeypatch

# Re-export common entry points and ensure subpackages are accessible as
# attributes on the top-level module for test-time monkeypatching via dotted
# paths like "flarchitect.core.architect.handle_one".
from .core.architect import Architect

try:
    __version__ = _get_version("flarchitect")
except PackageNotFoundError:  # pragma: no cover - fallback for editable installs
    __version__ = "0.0.0"

if not hasattr(werkzeug, "__version__"):
    try:  # pragma: no cover - best effort for older Werkzeug releases
        from werkzeug import __about__

        werkzeug.__version__ = __about__.__version__
    except Exception:  # pragma: no cover - maintain minimal fallback
        werkzeug.__version__ = "0"

__all__ = ["Architect", "__version__", "core", "authentication", "utils", "logging"]
