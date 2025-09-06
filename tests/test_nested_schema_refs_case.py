import json

import pytest

from demo.model_extension.model import create_app as create_app_models
from flarchitect.utils.core_utils import convert_case


@pytest.mark.parametrize("case", ["camel", "pascal"])
def test_nested_schema_refs_follow_case(case: str) -> None:
    app = create_app_models({"API_SCHEMA_CASE": case})
    client = app.test_client()
    spec = client.get("/docs/apispec.json").json
    spec_str = json.dumps(spec)
    expected = convert_case("Category", case)
    unexpected = "Category" if expected == "category" else "category"
    assert f"#/components/schemas/{expected}" in spec_str
    assert f"#/components/schemas/{unexpected}" not in spec_str
