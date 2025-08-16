"""Tests for response filtering utilities."""

from __future__ import annotations

from typing import Any

import pytest

from flarchitect.utils.response_filters import _filter_response_data


@pytest.mark.parametrize(
    "config, expected_keys",
    [
        (
            {
                "API_DUMP_DATETIME": True,
                "API_DUMP_VERSION": True,
                "API_DUMP_STATUS_CODE": True,
                "API_DUMP_RESPONSE_MS": True,
                "API_DUMP_TOTAL_COUNT": True,
                "API_DUMP_NULL_NEXT_URL": True,
                "API_DUMP_NULL_PREVIOUS_URL": True,
                "API_DUMP_NULL_ERRORS": True,
            },
            {
                "datetime",
                "api_version",
                "status_code",
                "response_ms",
                "total_count",
                "next_url",
                "previous_url",
                "errors",
                "payload",
            },
        ),
        (
            {
                "API_DUMP_DATETIME": False,
                "API_DUMP_VERSION": False,
                "API_DUMP_STATUS_CODE": False,
                "API_DUMP_RESPONSE_MS": False,
                "API_DUMP_TOTAL_COUNT": False,
                "API_DUMP_NULL_NEXT_URL": False,
                "API_DUMP_NULL_PREVIOUS_URL": False,
                "API_DUMP_NULL_ERRORS": False,
            },
            {"payload"},
        ),
        (
            {
                "API_DUMP_DATETIME": True,
                "API_DUMP_VERSION": False,
                "API_DUMP_STATUS_CODE": True,
                "API_DUMP_RESPONSE_MS": False,
                "API_DUMP_TOTAL_COUNT": True,
                "API_DUMP_NULL_NEXT_URL": True,
                "API_DUMP_NULL_PREVIOUS_URL": False,
                "API_DUMP_NULL_ERRORS": True,
            },
            {"datetime", "status_code", "total_count", "next_url", "errors", "payload"},
        ),
    ],
)
def test_filter_response_data_removes_and_keeps_keys(
    monkeypatch: pytest.MonkeyPatch, config: dict[str, bool], expected_keys: set[str]
) -> None:
    """Ensure ``_filter_response_data`` honors configuration switches.

    Args:
        monkeypatch: Pytest fixture for modifying objects during the test.
        config: Mapping of configuration flags to their desired values.
        expected_keys: Keys that should remain after filtering.
    """
    data: dict[str, Any] = {
        "datetime": "2024-01-01T00:00:00+00:00",
        "api_version": "v1",
        "status_code": 200,
        "response_ms": 10,
        "total_count": 3,
        "next_url": None,
        "previous_url": "",
        "errors": [],
        "payload": {"id": 1},
    }

    def fake_get_config_or_model_meta(
        key: str, *_, default: Any | None = None, **__
    ) -> Any:
        """Return configuration override for the given key."""
        return config.get(key, default)

    monkeypatch.setattr(
        "flarchitect.utils.response_filters.get_config_or_model_meta",
        fake_get_config_or_model_meta,
    )

    filtered = _filter_response_data(data.copy())
    expected = {k: data[k] for k in expected_keys}

    assert filtered == expected
