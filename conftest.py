import sys
from pathlib import Path

# Ensure the repository root is on sys.path when running tests from subdirectories.
ROOT_DIR: Path = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
