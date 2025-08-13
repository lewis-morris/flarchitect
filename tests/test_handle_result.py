import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Store existing module references so later tests can import the real package
ORIGINAL_MODULES = {
    name: sys.modules.get(name)
    for name in [
        "flarchitect",
        "flarchitect.utils",
        "flarchitect.utils.core_utils",
        "flarchitect.utils.config_helpers",
        "flarchitect.utils.general",
    ]
}

# Create stub packages to avoid executing flarchitect.__init__
flarchitect_pkg = types.ModuleType("flarchitect")
flarchitect_pkg.__path__ = [str(ROOT / "flarchitect")]
sys.modules["flarchitect"] = flarchitect_pkg

utils_pkg = types.ModuleType("flarchitect.utils")
utils_pkg.__path__ = [str(ROOT / "flarchitect" / "utils")]
sys.modules["flarchitect.utils"] = utils_pkg

# Load core_utils from file
spec = importlib.util.spec_from_file_location(
    "flarchitect.utils.core_utils",
    ROOT / "flarchitect" / "utils" / "core_utils.py",
)
core_utils = importlib.util.module_from_spec(spec)
sys.modules["flarchitect.utils.core_utils"] = core_utils
spec.loader.exec_module(core_utils)

# Stub ``config_helpers`` as it's not needed for these tests
config_helpers = types.ModuleType("flarchitect.utils.config_helpers")
config_helpers.get_config_or_model_meta = lambda *args, **kwargs: {}
sys.modules["flarchitect.utils.config_helpers"] = config_helpers

# Load the module under test
spec_general = importlib.util.spec_from_file_location("flarchitect.utils.general", ROOT / "flarchitect" / "utils" / "general.py")
general = importlib.util.module_from_spec(spec_general)
sys.modules["flarchitect.utils.general"] = general
spec_general.loader.exec_module(general)

handle_result = general.handle_result
HTTP_OK = general.HTTP_OK
HTTP_INTERNAL_SERVER_ERROR = general.HTTP_INTERNAL_SERVER_ERROR

# Restore any original modules so later imports see the real package
for name, module in ORIGINAL_MODULES.items():
    if module is not None:
        sys.modules[name] = module
    else:
        sys.modules.pop(name, None)


def test_handle_result_with_dict():
    data = {
        "query": [{"id": 1}, {"id": 2}],
        "total_count": 2,
        "next_url": "next",
        "previous_url": None,
    }
    status, value, count, next_url, previous_url = handle_result(data)
    assert status == HTTP_OK
    assert value == [{"id": 1}, {"id": 2}]
    assert count == 2
    assert next_url == "next"
    assert previous_url is None


def test_handle_result_with_tuple_status():
    result = ({"id": 1}, 201)
    status, value, count, next_url, previous_url = handle_result(result)
    assert status == 201
    assert value == {"id": 1}
    assert count == 1
    assert next_url is None and previous_url is None


def test_handle_result_error_dict():
    result = ({"errors": {"id": ["missing"]}}, HTTP_INTERNAL_SERVER_ERROR)
    status, value, count, *_ = handle_result(result)
    assert status == HTTP_INTERNAL_SERVER_ERROR
    assert "id" in value["errors"]
