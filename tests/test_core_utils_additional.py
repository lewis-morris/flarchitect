"""Additional tests for ``flarchitect.utils.core_utils`` helpers."""

from __future__ import annotations

from xml.etree import ElementTree as ET

import pytest

from flarchitect.utils.core_utils import (
    convert_camel_to_snake,
    convert_case,
    convert_kebab_to_snake,
    convert_snake_to_camel,
    dict_to_xml,
    get_count,
)


@pytest.mark.parametrize(
    ("source", "target_case", "expected"),
    [
        ("", "camel", ""),
        ("HTTP", "snake", "http"),
        ("MixedCaseInput", "kebab", "mixed-case-input"),
        ("version2Value", "snake", "version_2_value"),
        ("already_snake_case", "pascal", "AlreadySnakeCase"),
        ("kebab-case-string", "camel", "kebabCaseString"),
    ],
)
def test_convert_case_edge_inputs(source: str, target_case: str, expected: str) -> None:
    assert convert_case(source, target_case) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("_api_key", "_apiKey"),
        ("http_response_code", "httpResponseCode"),
    ],
)
def test_convert_snake_to_camel_preserves_leading_underscore(source: str, expected: str) -> None:
    assert convert_snake_to_camel(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("HTTPRequest", "http_request"),
        ("XMLParser", "xml_parser"),
        ("_InternalValue", "internal_value"),
    ],
)
def test_convert_camel_to_snake_handles_acronyms(source: str, expected: str) -> None:
    assert convert_camel_to_snake(source) == expected


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("api-endpoint", "api_endpoint"),
        ("API-ENDPOINT", "api_endpoint"),
    ],
)
def test_convert_kebab_to_snake_normalises_hyphenated_words(source: str, expected: str) -> None:
    assert convert_kebab_to_snake(source) == expected


def test_dict_to_xml_nested_structures() -> None:
    payload = {
        "user": {
            "name": "Alice",
            "roles": ["admin", "editor"],
        },
        "meta": {"active": True},
    }

    xml_output = dict_to_xml(payload)
    root = ET.fromstring(xml_output)

    assert root.tag == "root"
    user = root.find("user")
    assert user is not None
    assert user.findtext("name") == "Alice"
    roles = user.find("roles")
    assert roles is not None
    assert [item.text for item in roles.findall("item")] == ["admin", "editor"]

    meta = root.find("meta")
    assert meta is not None
    assert meta.findtext("active") == "true"


@pytest.mark.parametrize(
    ("result", "value", "expected"),
    [
        ({"total_count": 42}, [1, 2], 42),
        ({}, [1, 2, 3], 3),
        ({}, {"id": 1}, 1),
        ({}, [], 0),
        ({}, None, 0),
    ],
)
def test_get_count_various_inputs(result, value, expected) -> None:
    assert get_count(result, value) == expected
