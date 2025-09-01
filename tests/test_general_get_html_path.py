"""Tests for ``get_html_path`` helper."""

import importlib.util
import sys
import types
from pathlib import Path

from flask import Flask

# Create minimal stubs so ``general`` can be imported without the full package.
sys.modules.setdefault("flarchitect", types.ModuleType("flarchitect"))
utils_mod = types.ModuleType("flarchitect.utils")
config_helpers = types.ModuleType("flarchitect.utils.config_helpers")
core_utils = types.ModuleType("flarchitect.utils.core_utils")
config_helpers.get_config_or_model_meta = lambda *args, **kwargs: None
core_utils.convert_case = lambda value, case=None: value
core_utils.get_count = lambda *args, **kwargs: 0
utils_mod.config_helpers = config_helpers
utils_mod.core_utils = core_utils
sys.modules["flarchitect.utils"] = utils_mod
sys.modules["flarchitect.utils.config_helpers"] = config_helpers
sys.modules["flarchitect.utils.core_utils"] = core_utils

_general_spec = importlib.util.spec_from_file_location(
    "general",
    Path(__file__).resolve().parents[1] / "flarchitect" / "utils" / "general.py",
)
assert _general_spec and _general_spec.loader  # for mypy
_general = importlib.util.module_from_spec(_general_spec)
_general_spec.loader.exec_module(_general)
sys.modules["flarchitect.utils.general"] = _general

# Clean up stubbed modules to avoid polluting subsequent tests that import
# the real package. The loaded general module remains available via the
# explicit sys.modules entry above.
for _mod in [
    "flarchitect.utils.core_utils",
    "flarchitect.utils.config_helpers",
    "flarchitect.utils",
    "flarchitect",
]:
    sys.modules.pop(_mod, None)

get_html_path = _general.get_html_path


def test_get_html_path_falls_back() -> None:
    """``get_html_path`` should locate the package ``html`` directory without an app."""
    path = get_html_path()
    assert path.endswith("html")
    assert (Path(path) / "apispec.html").exists()


def test_get_html_path_uses_extension() -> None:
    """``get_html_path`` should use the registered extension when available."""
    app = Flask(__name__)

    class DummyExt:
        def get_templates_path(self) -> str:
            return "/tmp/custom_html"

    app.extensions["flarchitect"] = DummyExt()
    with app.app_context():
        assert get_html_path() == "/tmp/custom_html"
