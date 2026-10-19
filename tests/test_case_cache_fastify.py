"""Behavior and bounded-memory checks for repeated naming conversions."""

import hashlib
import json
import random
import string

import pytest

from flarchitect.utils import core_utils


@pytest.fixture(autouse=True)
def clear_conversion_cache():
    core_utils._convert_case_cached.cache_clear()
    yield
    core_utils._convert_case_cached.cache_clear()


@pytest.mark.parametrize(
    ("name", "style", "expected"),
    [
        ("", "camel", ""),
        ("___", "snake", "___"),
        ("HTTPResponse2XX", "camel", "httpResponse2Xx"),
        ("_private_key", "pascal", "PrivateKey"),
        ("naïve café", "snake", "na_ve_caf"),
        ("status_code", "screaming_kebab", "STATUS-CODE"),
        ("unchangedValue", "unknown", "unchangedValue"),
    ],
)
def test_conversion_edge_outputs(name, style, expected):
    assert core_utils.convert_case(name, style) == expected
    assert core_utils.convert_case(name, style) == expected
    assert core_utils._convert_case_cached.cache_info().hits == 1


def test_legacy_conversion_corpus_snapshot():
    # Captured before this change by the second-pass benchmark. Cover all styles,
    # punctuation, Unicode, acronym boundaries and deterministic mixed names.
    cases = ("camel", "pascal", "snake", "screaming_snake", "kebab", "screaming_kebab", "unknown")
    rng = random.Random(42)
    names = ["", "___", "HTTPResponse2XX", "_private_key", "naïve café", "status_code", "total_count", "next_url", "previous_url"]
    names += ["".join(rng.choices(string.ascii_letters + string.digits + "_- ", k=rng.randrange(1, 80))) for _ in range(200)]
    for _ in range(2):
        converted = [[name, case, core_utils.convert_case(name, case)] for name in names for case in cases]
        assert hashlib.sha256(json.dumps(converted).encode()).hexdigest() == "832701217693c83f1b45830faba4565c1ebe393000b4c782927e61629b3c9cb9"


def test_conversion_cache_is_bounded_and_evicts_oldest():
    for index in range(4097):
        core_utils.convert_case(f"field_{index}", "camel")
    info = core_utils._convert_case_cached.cache_info()
    assert info.maxsize == info.currsize == 4096
    core_utils.convert_case("field_4096", "camel")
    assert core_utils._convert_case_cached.cache_info().hits == 1
    core_utils.convert_case("field_0", "camel")
    assert core_utils._convert_case_cached.cache_info().misses == 4098
    assert core_utils._convert_case_cached.cache_info().currsize == 4096


class UnhashableString(str):
    __hash__ = None


@pytest.mark.parametrize(
    ("name", "style"),
    [
        ("a" * 257, "camel"),
        ("some_name", "a" * 257),
        (UnhashableString("some_name"), "camel"),
        ("", UnhashableString("camel")),
        (None, "camel"),
        (0, "camel"),
        ([], "camel"),
        ("some_name", None),
        ("", []),
    ],
)
def test_unusual_or_long_inputs_bypass_cache(name, style):
    expected = core_utils._convert_case_uncached(name, style)
    assert core_utils.convert_case(name, style) == expected
    assert core_utils._convert_case_cached.cache_info().currsize == 0
    assert core_utils._convert_case_cached.cache_info().misses == 0


@pytest.mark.parametrize(("name", "style"), [(1, "camel"), (b"some_name", "camel"), ("some_name", []), ("some_name", UnhashableString("camel"))])
def test_unusual_input_exceptions_are_preserved(name, style):
    with pytest.raises(TypeError) as original:
        core_utils._convert_case_uncached(name, style)
    with pytest.raises(TypeError) as cached:
        core_utils.convert_case(name, style)
    assert str(cached.value) == str(original.value)
    assert core_utils._convert_case_cached.cache_info().misses == 0


def test_exact_length_boundary_is_cached():
    name = "a" * 256
    style = "z" * 256
    assert core_utils.convert_case(name, style) == name
    assert core_utils.convert_case(name, style) == name
    assert core_utils._convert_case_cached.cache_info().hits == 1
