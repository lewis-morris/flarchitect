from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from flask import Flask


def _load_app() -> Flask:
    """Load a Flask application from ``FLASK_APP``.

    Returns:
        Flask: The application instance exported by the configured module.

    Raises:
        RuntimeError: If ``FLASK_APP`` is unset or the application cannot be loaded.
    """
    flask_app = os.environ.get("FLASK_APP")
    if not flask_app:
        raise RuntimeError("FLASK_APP environment variable is not set.")
    module_name, _, app_name = flask_app.partition(":")
    if not app_name:
        app_name = "app"
    module = importlib.import_module(module_name)
    try:
        app = getattr(module, app_name)
    except AttributeError as exc:  # pragma: no cover - defensive branch
        msg = f"{flask_app} does not export a Flask application."
        raise RuntimeError(msg) from exc
    return app


def _export_openapi(app: Flask, output_dir: Path) -> Path:
    """Export the application's OpenAPI specification to ``openapi.json``.

    Args:
        app: The Flask application whose spec will be exported.
        output_dir: Directory to write ``openapi.json`` into.

    Returns:
        Path: The path to the generated ``openapi.json`` file.
    """
    spec = app.extensions["flarchitect"].api_spec.to_dict()
    output_dir.mkdir(parents=True, exist_ok=True)
    spec_path = output_dir / "openapi.json"
    with spec_path.open("w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=2)
    return spec_path


def _generate_client(spec_path: Path, lang: str, output_dir: Path) -> None:
    """Generate a client library using ``openapi-generator`` if available.

    Args:
        spec_path: Path to the ``openapi.json`` specification file.
        lang: Target language for the generated client.
        output_dir: Directory to output the client code.
    """
    generator = shutil.which("openapi-generator") or shutil.which("openapi-generator-cli")
    if not generator:
        print("openapi-generator not installed; skipping client generation.", file=sys.stderr)
        return
    subprocess.run(
        [generator, "generate", "-i", str(spec_path), "-g", lang, "-o", str(output_dir)],
        check=True,
    )


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``flarchitect`` command-line interface.

    Args:
        argv: Optional list of command-line arguments. Defaults to ``sys.argv``.
    """
    parser = argparse.ArgumentParser(prog="flarchitect")
    subparsers = parser.add_subparsers(dest="command")

    client_parser = subparsers.add_parser("client", help="Generate an API client from the OpenAPI spec.")
    client_parser.add_argument("--lang", default="typescript", help="Target language for the client.")
    client_parser.add_argument("output_dir", help="Directory to output the client code.")

    args = parser.parse_args(argv)
    if args.command == "client":
        app = _load_app()
        spec_path = _export_openapi(app, Path(args.output_dir))
        _generate_client(spec_path, args.lang, Path(args.output_dir))
    else:  # pragma: no cover - fallback for missing command
        parser.print_help()
