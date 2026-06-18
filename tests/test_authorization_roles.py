from flask import Flask

from flarchitect.authorization.roles import _normalize_roles_spec, _resolve_required_roles


def test_normalize_roles_spec_supports_all_declared_shapes() -> None:
    assert _normalize_roles_spec(None) == (None, False)
    assert _normalize_roles_spec(True) == (None, False)
    assert _normalize_roles_spec("admin") == (["admin"], False)
    assert _normalize_roles_spec(["admin", 2]) == (["admin", "2"], False)
    assert _normalize_roles_spec(("admin", "editor")) == (["admin", "editor"], False)
    assert _normalize_roles_spec({"roles": "admin", "any_of": True}) == (["admin"], True)
    assert _normalize_roles_spec({"roles": ["admin", 3]}) == (["admin", "3"], False)
    assert _normalize_roles_spec({"roles": True, "any_of": True}) == (None, True)
    assert _normalize_roles_spec({"roles": object(), "any_of": True}) == (None, True)
    assert _normalize_roles_spec(123) == (None, False)


def test_resolve_required_roles_without_flask_context_returns_no_mapping() -> None:
    assert _resolve_required_roles("GET") == (None, False, None)


def test_resolve_required_roles_applies_single_spec_to_all_methods() -> None:
    app = Flask(__name__)
    app.config["API_ROLE_MAP"] = "admin"

    with app.app_context():
        assert _resolve_required_roles("POST") == (["admin"], False, "*")


def test_resolve_required_roles_uses_method_all_and_star_precedence() -> None:
    app = Flask(__name__)
    app.config["API_ROLE_MAP"] = {
        "GET": {"roles": ["reader"], "any_of": True},
        "POST": "writer",
        "ALL": ["fallback"],
        "*": ["star"],
    }

    with app.app_context():
        assert _resolve_required_roles("GET") == (["reader"], True, "GET")
        assert _resolve_required_roles("POST") == (["writer"], False, "POST")
        assert _resolve_required_roles("PATCH") == (["fallback"], False, "ALL")

    app.config["API_ROLE_MAP"] = {"*": ["star"]}
    with app.app_context():
        assert _resolve_required_roles("DELETE") == (["star"], False, "*")


def test_resolve_required_roles_handles_config_access_errors(monkeypatch) -> None:
    from flarchitect.authorization import roles as roles_module

    class BrokenCurrentApp:
        @property
        def config(self):
            raise RuntimeError("outside context")

    monkeypatch.setattr(roles_module, "current_app", BrokenCurrentApp())

    assert roles_module._resolve_required_roles("GET") == (None, False, None)
