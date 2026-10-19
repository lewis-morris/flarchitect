"""Configuration memoization must isolate sources and request lifetimes."""

import pytest
from flask import Flask, g

from flarchitect.utils.config_helpers import get_config_or_model_meta


def _source(name, value):
    return type(name, (), {"Meta": type("Meta", (), {"foo": value})})


@pytest.mark.parametrize("slot", ["model", "output_schema", "input_schema"])
def test_same_name_source_classes_do_not_share_configuration(slot):
    first = _source("SameName", "first")
    second = _source("SameName", "second")
    with Flask(__name__).test_request_context("/"):
        assert get_config_or_model_meta("foo", **{slot: first}) == "first"
        assert get_config_or_model_meta("foo", **{slot: second}) == "second"
        assert get_config_or_model_meta("foo", **{slot: first}) == "first"


@pytest.mark.parametrize("slot", ["model", "output_schema", "input_schema"])
def test_unhashable_equal_instances_use_their_own_metadata(slot):
    class Source:
        __hash__ = None

        def __eq__(self, other):
            return True

    first, second = Source(), Source()
    first.Meta = _source("First", "first").Meta
    second.Meta = _source("Second", "second").Meta
    with Flask(__name__).test_request_context("/"):
        assert get_config_or_model_meta("foo", **{slot: first}) == "first"
        assert get_config_or_model_meta("foo", **{slot: second}) == "second"
        assert get_config_or_model_meta("foo", **{slot: first}) == "first"


def test_sequential_requests_in_same_app_context_have_separate_caches():
    app = Flask(__name__)
    with app.app_context():
        app.config["API_FOO"] = "first"
        with app.test_request_context("/"):
            assert get_config_or_model_meta("foo") == "first"
            first_cache = g._flarch_cfg_cache
        app.config["API_FOO"] = "second"
        with app.test_request_context("/"):
            assert get_config_or_model_meta("foo") == "second"
            assert g._flarch_cfg_cache is not first_cache


def test_nested_requests_restore_outer_cache_and_introspection_alias():
    app = Flask(__name__)
    with app.test_request_context("/outer"):
        app.config["API_FOO"] = "outer"
        assert get_config_or_model_meta("foo") == "outer"
        outer_cache = g._flarch_cfg_cache
        with app.test_request_context("/inner"):
            app.config["API_FOO"] = "inner"
            assert get_config_or_model_meta("foo") == "inner"
            assert g._flarch_cfg_cache is not outer_cache
        assert get_config_or_model_meta("foo") == "outer"
        assert g._flarch_cfg_cache is outer_cache


def test_cached_source_stays_alive_until_request_cache_is_released():
    import gc
    import weakref

    class Source:
        class Meta:
            foo = "value"

    app = Flask(__name__)
    with app.test_request_context("/"):
        source = Source()
        reference = weakref.ref(source)
        assert get_config_or_model_meta("foo", output_schema=source) == "value"
        del source
        gc.collect()
        assert reference() is not None
    gc.collect()
    assert reference() is None
