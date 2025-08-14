from flask import Flask

from flarchitect.specs.utils import scrape_extra_info_from_spec_data


def test_scrape_extra_info_logs_missing_fields(monkeypatch):
    """scrape_extra_info_from_spec_data should report which fields are missing."""
    messages: list[str] = []

    def fake_log(level: int, message: str) -> None:
        messages.append(message)

    monkeypatch.setattr("flarchitect.logging.logger.log", fake_log)
    app = Flask(__name__)
    with app.app_context():
        scrape_extra_info_from_spec_data({"function": lambda: None}, method="GET")
    assert any("model" in msg and "schema" in msg for msg in messages)
