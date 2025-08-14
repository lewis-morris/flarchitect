import importlib.util
from pathlib import Path

import pytest
from flask import Flask

spec_utils_path = (
    Path(__file__).resolve().parents[1] / "flarchitect" / "specs" / "utils.py"
)
spec_utils_spec = importlib.util.spec_from_file_location("spec_utils", spec_utils_path)
spec_utils_module = importlib.util.module_from_spec(spec_utils_spec)
assert spec_utils_spec.loader is not None  # for mypy
spec_utils_spec.loader.exec_module(spec_utils_module)

convert_path_to_openapi = spec_utils_module.convert_path_to_openapi
scrape_extra_info_from_spec_data = spec_utils_module.scrape_extra_info_from_spec_data


def test_scrape_extra_info_logs_missing_fields(monkeypatch):
    """scrape_extra_info_from_spec_data should report which fields are missing."""
    messages: list[str] = []

    def fake_log(level: int, message: str) -> None:
        messages.append(message)

    monkeypatch.setattr("flarchitect.logging.logger.log", fake_log)
    app = Flask(__name__)
    with app.app_context():
        scrape_extra_info_from_spec_data({"function": lambda: None}, method="GET")
    assert any("model" in msg and "schema" in msg for msg in messages)


@pytest.mark.parametrize(
    ("flask_path", "openapi_path"),
    [
        ("/users/<int:id>", "/users/{id}"),
        ("/files/<path:filepath>", "/files/{filepath}"),
        ("/items/<uuid:item_id>", "/items/{item_id}"),
        ("/simple/<name>", "/simple/{name}"),
    ],
)
def test_convert_path_to_openapi(flask_path: str, openapi_path: str) -> None:
    """convert_path_to_openapi should replace Flask converters with OpenAPI params."""
    assert convert_path_to_openapi(flask_path) == openapi_path
