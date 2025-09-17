import types
from pathlib import Path

import pytest

from flarchitect.utils.general import (
    check_rate_services,
    generate_readme_html,
    normalize_key,
    pluralize_last_word,
    validate_flask_limiter_rate_limit_string,
    xml_to_dict,
)


def test_rate_limit_uri_configured_variants():
    # memory backend without host
    cfg = lambda key, default=None: "memory://" if key == "API_RATE_LIMIT_STORAGE_URI" else default
    assert check_rate_services(config_getter=cfg) == "memory://"

    # redis with host triggers prereq checker
    cfg = lambda key, default=None: "redis://127.0.0.1:6379" if key == "API_RATE_LIMIT_STORAGE_URI" else default
    assert check_rate_services(config_getter=cfg, prereq_checker=lambda *_: None) == "redis://127.0.0.1:6379"

    # invalid URI scheme
    cfg = lambda key, default=None: "foo://127.0.0.1:1" if key == "API_RATE_LIMIT_STORAGE_URI" else default
    with pytest.raises(ValueError):
        check_rate_services(config_getter=cfg)

    # missing host for non-memory
    cfg = lambda key, default=None: "redis://" if key == "API_RATE_LIMIT_STORAGE_URI" else default
    with pytest.raises(ValueError):
        check_rate_services(config_getter=cfg)


def test_rate_limit_autodetect_disabled_and_socket_blocked():
    cfg = lambda key, default=None: False if key == "API_RATE_LIMIT_AUTODETECT" else default
    assert check_rate_services(config_getter=cfg) is None

    # Simulate socket permission error (e.g. sandbox) -> returns None
    class DenySocket:
        def __call__(self, *_args, **_kwargs):
            raise PermissionError

    cfg_default = lambda key, default=None: default
    assert check_rate_services(config_getter=cfg_default, socket_factory=DenySocket()) is None


def test_validate_rate_limit_string_and_helpers():
    assert validate_flask_limiter_rate_limit_string("10 per second")
    assert validate_flask_limiter_rate_limit_string("100 per minutes")
    assert not validate_flask_limiter_rate_limit_string("ten per second")

    assert pluralize_last_word("user") == "users"
    assert pluralize_last_word("UserName") == "UserNames"
    assert normalize_key("abc") == "ABC"


def test_xml_to_dict_valid_and_invalid():
    xml = "<root><a>1</a><b/></root>"
    out = xml_to_dict(xml)
    assert out == {"root": {"a": "1", "b": None}}
    with pytest.raises(ValueError):
        xml_to_dict("<not-xml")


def test_generate_readme_html_smoke():
    # Uses repository README as a plain text Jinja2 template
    path = Path("README.md")
    if path.exists():
        rendered = generate_readme_html("README.md")
        assert isinstance(rendered, str)
        assert len(rendered) > 0
