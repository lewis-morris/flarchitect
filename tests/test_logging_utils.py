"""Tests for logging utilities."""

import importlib.util
from importlib.machinery import ModuleSpec
from pathlib import Path

from colorama import Fore

# Import the logging module directly to avoid package-level imports requiring external deps.
project_root = Path(__file__).resolve().parents[1]
spec: ModuleSpec | None = importlib.util.spec_from_file_location(
    "flarchitect_logging",
    project_root / "flarchitect" / "logging.py",
)
flarchitect_logging = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(flarchitect_logging)
CustomLogger = flarchitect_logging.CustomLogger
color_text_with_multiple_patterns = flarchitect_logging.color_text_with_multiple_patterns


def test_color_text_with_multiple_patterns_replaces_wrappers() -> None:
    text = "This is `code`, +danger+, --info--, $price$, and |success|."
    colored = color_text_with_multiple_patterns(text)
    assert Fore.YELLOW in colored
    assert Fore.RED in colored
    assert Fore.CYAN in colored
    assert Fore.MAGENTA in colored
    assert Fore.GREEN in colored
    assert "`code`" not in colored
    assert "+danger+" not in colored
    assert "--info--" not in colored
    assert "$price$" not in colored
    assert "|success|" not in colored


def test_custom_logger_respects_verbosity(capsys) -> None:
    logger = CustomLogger(verbosity_level=1)
    logger.log(1, "hi")
    out = capsys.readouterr().out
    assert "LOG 1:" in out

    logger.log(2, "no")
    out = capsys.readouterr().out
    assert out == ""


def test_custom_logger_error_color(capsys) -> None:
    logger = CustomLogger(verbosity_level=1)
    logger.error(1, "boom")
    out = capsys.readouterr().out
    assert "ERROR 1:" in out
    assert Fore.RED in out
