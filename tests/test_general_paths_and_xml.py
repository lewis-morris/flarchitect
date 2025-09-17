import os
from pathlib import Path

from flask import Flask

from flarchitect.utils.config_helpers import is_xml
from flarchitect.utils.general import find_child_from_parent_dir


def test_find_child_from_parent_dir(tmp_path: Path, monkeypatch):
    # Create structure: tmp/foo/bar
    base = tmp_path / "foo" / "bar"
    base.mkdir(parents=True)
    # search starting at tmp_path
    found = find_child_from_parent_dir("foo", "bar", current_dir=str(tmp_path))
    assert found == str(base)


def test_is_xml_accept_and_content_type():
    app = Flask(__name__)
    with app.app_context():
        with app.test_request_context("/", headers={"Accept": "application/xml"}):
            assert is_xml() is True
        with app.test_request_context("/", headers={"Content-Type": "text/xml"}):
            assert is_xml() is True
