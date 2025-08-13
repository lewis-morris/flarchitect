"""Tests for ensuring ``CustomSpec`` uses instance-specific containers."""

from flask import Flask

from flarchitect.specs.generator import CustomSpec


class DummyArchitect:
    """Minimal architect stub for CustomSpec tests."""

    def __init__(self, app: Flask) -> None:
        self.app = app
        self.route_spec: list[dict] = []

    def get_templates_path(self) -> str:
        """Return dummy templates path required by CustomSpec."""
        return ""


def _create_spec() -> CustomSpec:
    """Create a ``CustomSpec`` with docs generation disabled."""
    app = Flask(__name__)
    app.config["API_CREATE_DOCS"] = False
    app.config["API_DESCRIPTION"] = "desc"
    architect = DummyArchitect(app)
    with app.app_context():
        return CustomSpec(app, architect)


def test_spec_groups_are_instance_specific() -> None:
    """Each ``CustomSpec`` should maintain its own ``spec_groups``."""
    spec_one = _create_spec()
    spec_two = _create_spec()

    spec_one.set_xtags_group("tag1", "group1")

    assert spec_one.spec_groups["x-tagGroups"] == [{"name": "group1", "tags": ["tag1"]}]
    assert spec_two.spec_groups == {"x-tagGroups": []}


def test_api_keywords_are_instance_specific() -> None:
    """Each ``CustomSpec`` should maintain its own ``api_keywords`` list."""
    spec_one = _create_spec()
    spec_two = _create_spec()

    spec_one.api_keywords.append("keyword")

    assert spec_one.api_keywords == ["keyword"]
    assert spec_two.api_keywords == []


def test_to_dict_handles_none_spec_groups() -> None:
    """``to_dict`` should not fail when ``spec_groups`` is ``None``."""
    spec = _create_spec()
    spec.spec_groups = None

    spec_dict = spec.to_dict()

    assert "x-tagGroups" not in spec_dict
