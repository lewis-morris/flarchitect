"""Request configuration cache behavior and avoided lookup work."""

from unittest.mock import patch

from flask import Flask

from flarchitect.utils import config_helpers


def test_positive_cache_hits_skip_lookup_preparation():
    app = Flask(__name__)
    app.config["API_FOO"] = "configured"
    with app.test_request_context("/"), patch.object(config_helpers, "_method_based_keys", wraps=config_helpers._method_based_keys) as prepare:
        for _ in range(3):
            assert config_helpers.get_config_or_model_meta("FOO") == "configured"
        assert prepare.call_count == 1


def test_defaults_are_not_cached_and_configuration_can_appear():
    app = Flask(__name__)
    with app.test_request_context("/"):
        assert config_helpers.get_config_or_model_meta("FOO", default="first", return_from_config=True) == ("first", "default")
        assert config_helpers.get_config_or_model_meta("FOO", default="second", return_from_config=True) == ("second", "default")
        app.config["API_FOO"] = "configured"
        assert config_helpers.get_config_or_model_meta("FOO", return_from_config=True) == ("configured", "config")


def test_method_metadata_precedence_survives_cache_hits():
    class Model:
        class Meta:
            get_foo = "model get"
            foo = "model fallback"

    app = Flask(__name__)
    app.config.update(API_GET_FOO="config get", API_FOO="config fallback")
    with app.test_request_context("/"):
        for _ in range(2):
            assert config_helpers.get_config_or_model_meta("API_FOO", model=Model, method="GET", return_from_config=True) == ("model get", "model")
            assert config_helpers.get_config_or_model_meta("API_FOO", model=Model, method="POST", return_from_config=True) == ("model fallback", "model")
            assert config_helpers.get_config_or_model_meta("API_FOO", method="GET", return_from_config=True) == ("config get", "config")


def test_configuration_cache_does_not_cross_requests():
    app = Flask(__name__)
    app.config["API_FOO"] = "first"
    with app.test_request_context("/"):
        assert config_helpers.get_config_or_model_meta("FOO") == "first"
        app.config["API_FOO"] = "second"
        assert config_helpers.get_config_or_model_meta("FOO") == "first"
    with app.test_request_context("/"):
        assert config_helpers.get_config_or_model_meta("FOO") == "second"
