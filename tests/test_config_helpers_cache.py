from flask import Flask, g

from flarchitect.utils.config_helpers import get_config_or_model_meta


def test_get_config_or_model_meta_caches_in_request_context():
    app = Flask(__name__)
    app.config["API_FOO"] = True
    with app.app_context():
        with app.test_request_context("/"):
            # first call populates cache
            assert get_config_or_model_meta("FOO", default=False) is True
            # mutate to verify cached value returned despite config change
            app.config["API_FOO"] = False
            assert get_config_or_model_meta("FOO", default=False) is True
            # cache object exists
            assert hasattr(g, "_flarch_cfg_cache")
