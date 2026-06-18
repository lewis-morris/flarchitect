from typing import ClassVar

from flask import Flask, g

from flarchitect.utils.config_helpers import get_config_or_model_meta


class _Model:
    class Meta:
        block_methods: ClassVar[list[str]] = ["POST"]


class _OutputSchema:
    class Meta:
        block_methods: ClassVar[list[str]] = ["PATCH"]


class _InputSchema:
    class Meta:
        block_methods: ClassVar[list[str]] = ["DELETE"]


def test_get_config_or_model_meta_caches_in_request_context():
    app = Flask(__name__)
    app.config["API_FOO"] = True
    with app.app_context(), app.test_request_context("/"):
        # first call populates cache
        assert get_config_or_model_meta("FOO", default=False) is True
        # mutate to verify cached value returned despite config change
        app.config["API_FOO"] = False
        assert get_config_or_model_meta("FOO", default=False) is True
        # cache object exists
        assert hasattr(g, "_flarch_cfg_cache")


def test_get_config_or_model_meta_joins_list_metadata_sources():
    result = get_config_or_model_meta(
        "BLOCK_METHODS",
        model=_Model,
        output_schema=_OutputSchema(),
        input_schema=_InputSchema(),
        default=[],
        allow_join=True,
    )

    assert result == ["POST", "PATCH", "DELETE"]
