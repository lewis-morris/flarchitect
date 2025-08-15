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
endpoint_namer = spec_utils_module.endpoint_namer


def test_scrape_extra_info_logs_missing_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """scrape_extra_info_from_spec_data should report which fields are missing."""
    from flarchitect.logging import logger

    app = Flask(__name__)
    original_level = logger.verbosity_level
    logger.verbosity_level = 1
    try:
        with app.app_context():
            scrape_extra_info_from_spec_data({"function": lambda: None}, method="GET")
    finally:
        logger.verbosity_level = original_level
    captured = capsys.readouterr().out
    assert "model" in captured and "schema" in captured


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


def test_endpoint_namer_accepts_model_and_schemas() -> None:
    """endpoint_namer should derive names from a model or schemas."""

    class Widget:
        pass

    class InputSchema:
        class Meta:
            model = Widget

    class OutputSchema:
        class Meta:
            model = Widget

    app = Flask(__name__)
    with app.app_context():
        assert endpoint_namer(Widget) == "widgets"
        assert endpoint_namer(input_schema=InputSchema) == "widgets"
        assert endpoint_namer(output_schema=OutputSchema) == "widgets"
        with pytest.raises(ValueError):
            endpoint_namer()


def test_endpoint_namer_respects_config_case() -> None:
    """endpoint_namer should honour ``API_ENDPOINT_CASE`` setting."""

    class Widget:
        pass

    app = Flask(__name__)
    with app.app_context():
        app.config["API_ENDPOINT_CASE"] = "pascal"
        assert endpoint_namer(Widget) == "Widgets"
