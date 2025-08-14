from flask import Flask

from flarchitect import Architect


def _create_app() -> Flask:
    """Create a minimal Flask app for testing."""
    app = Flask(__name__)
    app.config.update(FULL_AUTO=False, API_CREATE_DOCS=False)
    return app


def test_architect_skips_init_in_reloader(monkeypatch):
    """Architect should skip initialisation in the reloader parent process."""
    app = _create_app()
    monkeypatch.delenv("WERKZEUG_RUN_MAIN", raising=False)
    monkeypatch.setenv("WERKZEUG_SERVER_FD", "3")

    architect = Architect(app)
    assert not hasattr(architect, "app")


def test_architect_init_runs_when_reloader_child(monkeypatch):
    """Initialisation should run in the serving process."""
    app = _create_app()
    monkeypatch.setenv("WERKZEUG_RUN_MAIN", "true")
    monkeypatch.setenv("WERKZEUG_SERVER_FD", "3")

    with app.app_context():
        architect = Architect(app)
        assert architect.app is app


def test_documentation_url_logged(monkeypatch):
    """The documentation URL should be logged on startup."""
    app = Flask(__name__)
    app.config.update(FULL_AUTO=False, API_DESCRIPTION="Test API")
    messages: list[str] = []

    def fake_log(level: int, message: str) -> None:
        messages.append(message)

    monkeypatch.setattr("flarchitect.logging.logger.log", fake_log)
    with app.app_context():
        Architect(app)
    assert any("|/docs|" in msg for msg in messages)
