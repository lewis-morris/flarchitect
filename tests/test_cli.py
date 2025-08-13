import importlib
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

# Load CLI module without importing the full package
CLI_PATH = Path(__file__).resolve().parents[1] / "flarchitect" / "cli.py"
spec = importlib.util.spec_from_file_location("cli", CLI_PATH)
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def _write_app(tmp_path: Path) -> None:
    module_path = tmp_path / "appmodule.py"
    module_path.write_text(
        "from flask import Flask\n"
        "app = Flask(__name__)\n"
        "class DummySpec:\n"
        "    def to_dict(self):\n"
        "        return {'openapi': '3.0.2'}\n"
        "class DummyExt:\n"
        "    api_spec = DummySpec()\n"
        "app.extensions = {'flarchitect': DummyExt()}\n"
    )
    sys.path.insert(0, str(tmp_path))


@pytest.fixture
def app_env(tmp_path, monkeypatch):
    _write_app(tmp_path)
    monkeypatch.setenv("FLASK_APP", "appmodule:app")
    yield tmp_path
    sys.path.remove(str(tmp_path))


def test_client_generates_openapi_and_invokes_generator(app_env, monkeypatch):
    output_dir = app_env / "client"
    run_mock = mock.Mock()
    monkeypatch.setattr(cli, "subprocess", mock.Mock(run=run_mock))
    monkeypatch.setattr(cli.shutil, "which", lambda x: "/usr/bin/openapi-generator")

    cli.main(["client", "--lang", "typescript", str(output_dir)])

    spec_path = output_dir / "openapi.json"
    assert spec_path.exists()
    data = json.loads(spec_path.read_text())
    assert data.get("openapi")
    run_mock.assert_called_once()


def test_client_handles_missing_generator(app_env, monkeypatch, capsys):
    output_dir = app_env / "client"
    monkeypatch.setattr(cli.shutil, "which", lambda x: None)
    run_mock = mock.Mock()
    monkeypatch.setattr(cli.subprocess, "run", run_mock)

    cli.main(["client", str(output_dir)])

    spec_path = output_dir / "openapi.json"
    assert spec_path.exists()
    assert not run_mock.called
    captured = capsys.readouterr()
    assert "not installed" in captured.err
