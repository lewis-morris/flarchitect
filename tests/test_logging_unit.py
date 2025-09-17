import json

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

