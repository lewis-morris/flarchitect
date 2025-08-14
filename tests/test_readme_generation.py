from pathlib import Path

from flarchitect.utils.general import generate_readme_html


def test_generate_readme_html_accepts_path_object() -> None:
    config = {"API_AUTHENTICATE": False, "API_TITLE": "Example"}
    path = Path("flarchitect/html/base_readme.MD")
    rendered = generate_readme_html(path, config=config, api_output_example="{}", has_rate_limiting=False)
    assert "Example" in rendered
