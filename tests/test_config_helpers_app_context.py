from flask import Flask

from flarchitect.utils.config_helpers import get_config_or_model_meta


def test_get_config_or_model_meta_in_app_context_without_request():
    app = Flask(__name__)
    app.config["API_FOO_BAR"] = "baz"
    with app.app_context():
        assert get_config_or_model_meta("FOO_BAR") == "baz"

