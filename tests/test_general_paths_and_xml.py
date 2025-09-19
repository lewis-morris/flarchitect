from pathlib import Path

import pytest
from flask import Flask
from jinja2 import TemplateNotFound

from flarchitect.utils.config_helpers import is_xml
from flarchitect.utils import general as general_utils


def test_find_html_directory_handles_nested_levels(tmp_path: Path) -> None:
    level_one = tmp_path / "level_one"
    level_two = level_one / "level_two"
    (level_two / "html").mkdir(parents=True)

    found = general_utils.find_html_directory(str(level_two))
    assert found == str(level_two / "html")


def test_find_html_directory_walks_up_to_parent(tmp_path: Path) -> None:
    root = tmp_path / "pkg"
    html_dir = root / "html"
    deep = root / "a" / "b" / "c"
    html_dir.mkdir(parents=True)
    deep.mkdir(parents=True)

    found = general_utils.find_html_directory(str(deep))
    assert found == str(html_dir)


def test_find_html_directory_returns_none_when_absent(tmp_path: Path) -> None:
    (tmp_path / "pkg").mkdir()
    assert general_utils.find_html_directory(str(tmp_path / "pkg")) is None


def test_get_html_path_returns_empty_when_unresolved(monkeypatch):
    monkeypatch.setattr(general_utils, "find_html_directory", lambda: None)
    assert general_utils.get_html_path() == ""


def test_manual_render_absolute_template_renders(tmp_path: Path, monkeypatch) -> None:
    templates_root = tmp_path / "templates"
    templates_root.mkdir()
    (templates_root / "greeting.html").write_text("Hello {{ name }}")

    monkeypatch.setattr(general_utils, "get_html_path", lambda: str(tmp_path))
    rendered = general_utils.manual_render_absolute_template("templates/greeting.html", name="World")
    assert rendered == "Hello World"


def test_manual_render_absolute_template_missing_template(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "templates").mkdir()
    monkeypatch.setattr(general_utils, "get_html_path", lambda: str(tmp_path))

    with pytest.raises(TemplateNotFound):
        general_utils.manual_render_absolute_template("templates/missing.html")


def test_manual_render_absolute_template_bad_directory(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(general_utils, "get_html_path", lambda: str(tmp_path))

    with pytest.raises(TemplateNotFound):
        general_utils.manual_render_absolute_template("nope/also_missing.html")


def test_find_child_from_parent_dir(tmp_path: Path, monkeypatch):
    # Create structure: tmp/foo/bar
    base = tmp_path / "foo" / "bar"
    base.mkdir(parents=True)
    # search starting at tmp_path
    found = general_utils.find_child_from_parent_dir("foo", "bar", current_dir=str(tmp_path))
    assert found == str(base)


def test_find_child_from_parent_dir_returns_none(tmp_path: Path):
    (tmp_path / "foo").mkdir()
    assert general_utils.find_child_from_parent_dir("foo", "missing", current_dir=str(tmp_path)) is None


def test_find_child_from_parent_dir_deeply_nested(tmp_path: Path):
    start = tmp_path / "outer" / "inner"
    target_parent = start / "root"
    target = target_parent / "target"
    target.mkdir(parents=True)

    found = general_utils.find_child_from_parent_dir("root", "target", current_dir=str(tmp_path))
    assert found == str(target)


def test_is_xml_accept_and_content_type():
    app = Flask(__name__)
    with app.app_context():
        with app.test_request_context("/", headers={"Accept": "application/xml"}):
            assert is_xml() is True
        with app.test_request_context("/", headers={"Content-Type": "text/xml"}):
            assert is_xml() is True
