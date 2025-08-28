"""Pytest configuration and shared fixtures.

Extends sys.path to include the project root and re-exports selected fixtures
so they are available across the entire test suite regardless of plugin load
order.
"""

import sys
from pathlib import Path

# Resolve root directory of repository.
ROOT_DIR: Path = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Re-export key fixtures used by multiple modules
try:  # pragma: no cover - fixture re-export
    from tests.test_authentication import client_jwt  # noqa: F401
except Exception:
    pass
