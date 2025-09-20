import json
import time

from colorama import Fore
from flask import Flask, g

from flarchitect.logging import CustomLogger, color_text_with_multiple_patterns, get_logger


def test_color_text_replacements_basic():
    text = "see `code` +warn+ --note-- $money$ |pipe|"
    colored = color_text_with_multiple_patterns(text)
    # patterns removed, replaced by colorized contents
    assert "`code`" not in colored
    assert "+warn+" not in colored
    assert "--note--" not in colored
    assert "$money$" not in colored
    assert "|pipe|" not in colored
    # but inner texts remain
    for inner in ("code", "warn", "note", "money", "pipe"):
        assert inner in colored


def test_color_text_with_overlapping_and_multiple_patterns():
    text = "prefix +--warn--+ $value$ suffix"
    coloured = color_text_with_multiple_patterns(text)
    assert "+--warn--+" not in coloured
    assert "$value$" not in coloured
    assert "warn" in coloured and "value" in coloured


def test_color_text_without_patterns_returns_original():
    text = "plain text without markers"
    assert color_text_with_multiple_patterns(text) == text


def test_logger_text_and_json_modes(capsys):
    lg = CustomLogger(verbosity_level=3)
    lg.log(2, "hello")
    lg.debug(4, "too-verbose")  # should not emit
    lg.error(3, "boom")  # text mode
    captured = capsys.readouterr().out
    assert "hello" in captured
    assert "too-verbose" not in captured
    assert "boom" in captured

    # JSON mode
    lg.json_mode = True
    lg.error(3, "json-boom")
    line = capsys.readouterr().out.strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["event"] == "error"
    assert payload["message"] == "json-boom"
    assert payload["lvl"] == 3


def test_get_logger_singleton():
    assert get_logger() is get_logger()


def test_logger_prefix_and_colour(capsys):
    lg = CustomLogger(verbosity_level=5)
    lg.log(4, "info message")
    lg.debug(5, "debug message")
    lg.error(4, "error message")

    captured = capsys.readouterr().out.splitlines()
    assert captured[0].strip().startswith("LOG 4:")
    assert captured[1].strip().startswith("DEBUG 5:")
    assert captured[2].startswith(Fore.RED)
    assert "error message" in captured[2]


def test_logger_suppression_when_above_verbosity(capsys):
    lg = CustomLogger(verbosity_level=1)
    lg.log(2, "suppressed")
    lg.error(3, "also suppressed")
    lg.debug(0, "visible")
    output = capsys.readouterr().out
    assert "suppressed" not in output
    assert "visible" in output


def test_logger_context_in_json_mode(capsys):
    app = Flask(__name__)
    lg = CustomLogger(verbosity_level=5)
    lg.json_mode = True

    with app.test_request_context("/ctx", method="POST"):
        g.request_id = "req-123"
        g._flarch_req_start = time.perf_counter() - 0.05
        lg.log(2, "context message")

    line = capsys.readouterr().out.strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["event"] == "log"
    assert payload["message"] == "context message"
    assert payload["method"] == "POST"
    assert payload["path"] == "/ctx"
    assert payload["request_id"] == "req-123"
    assert isinstance(payload["latency_ms"], int)
