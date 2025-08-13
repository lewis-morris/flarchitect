"""Tests for instance-level initialization of mutable defaults."""

from flask import Flask

from flarchitect import Architect
from flarchitect.core.routes import RouteCreator
from flarchitect.specs.generator import register_routes_with_spec


def test_architect_route_spec_isolated() -> None:
    """Route specifications should be unique per :class:`Architect` instance."""

    app1 = Flask("app1")
    app1.config.update(FULL_AUTO=False, API_CREATE_DOCS=False)
    with app1.app_context():
        arch1 = Architect(app1)

    app2 = Flask("app2")
    app2.config.update(FULL_AUTO=False, API_CREATE_DOCS=False)
    with app2.app_context():
        arch2 = Architect(app2)

    def dummy() -> None:  # pragma: no cover - simple placeholder
        return None

    arch1.set_route({"function": dummy})

    assert len(arch1.route_spec) == 1
    assert arch2.route_spec == []
    assert arch1.route_spec is not arch2.route_spec


def test_route_creator_created_routes_isolated() -> None:
    """Created routes should be unique per :class:`RouteCreator` instance."""

    app = Flask(__name__)
    app.config.update(FULL_AUTO=False, API_CREATE_DOCS=False)
    with app.app_context():
        arch = Architect(app)

        rc1 = RouteCreator(architect=arch, app=app, api_full_auto=False)
        rc2 = RouteCreator(architect=arch, app=app, api_full_auto=False)

    rc1._add_to_created_routes(
        name="test",
        method="GET",
        url="/test",
        model=None,
        input_schema=None,
        output_schema=None,
    )

    assert "test" in rc1.created_routes
    assert rc2.created_routes == {}
    assert rc1.created_routes is not rc2.created_routes


def test_register_routes_with_spec_none() -> None:
    """``register_routes_with_spec`` handles ``None`` gracefully."""

    app = Flask(__name__)
    app.config.update(FULL_AUTO=False, API_CREATE_DOCS=False)
    with app.app_context():
        arch = Architect(app)

        # Should not raise when route_spec is ``None``
        register_routes_with_spec(arch, None)
