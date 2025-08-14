"""Tests for response data filtering utility."""

from __future__ import annotations

from typing import Any

import pytest

from flarchitect.utils.response_filters import _filter_response_data


@pytest.mark.parametrize(
    ("config_overrides", "removed"),
    [
        ({}, {"errors"}),
        ({"API_DUMP_DATETIME": False}, {"errors", "datetime"}),
        ({"API_DUMP_VERSION": False}, {"errors", "api_version"}),
        ({"API_DUMP_STATUS_CODE": False}, {"errors", "status_code"}),
        ({"API_DUMP_RESPONSE_MS": False}, {"errors", "response_ms"}),
        ({"API_DUMP_TOTAL_COUNT": False}, {"errors", "total_count"}),
        ({"API_DUMP_NULL_NEXT_URL": False}, {"errors", "next_url"}),
        ({"API_DUMP_NULL_PREVIOUS_URL": False}, {"errors", "previous_url"}),
        ({"API_DUMP_NULL_ERRORS": True}, set()),
        (
            {
                "API_DUMP_DATETIME": False,
                "API_DUMP_RESPONSE_MS": False,
                "API_DUMP_NULL_NEXT_URL": False,
            },
            {"errors", "datetime", "response_ms", "next_url"},
        ),
    ],
)
def test_filter_response_data(
    config_overrides: dict[str, Any], removed: set[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Filter response data according to configuration settings."""
    base = {
        "datetime": "2023-01-01",
        "api_version": "1",
        "status_code": 200,
        "response_ms": 5,
        "total_count": 1,
        "next_url": "",
        "previous_url": "",
        "errors": [],
    }

    def fake_getter(
        key: str, *args: Any, default: Any | None = None, **kwargs: Any
    ) -> Any:
        return config_overrides.get(key, default)

    monkeypatch.setattr(
        "flarchitect.utils.response_filters.get_config_or_model_meta",
        fake_getter,
    )

    result = _filter_response_data(base.copy())
    expected_keys = set(base) - removed
    assert set(result) == expected_keys
