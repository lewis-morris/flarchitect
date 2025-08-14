"""Pytest configuration to add project root to sys.path."""

import sys
from pathlib import Path

# Resolve root directory of repository.
ROOT_DIR: Path = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
