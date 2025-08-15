"""Tests for rate limit service utilities."""

from __future__ import annotations

import importlib.util

import pytest

from flarchitect.utils.general import check_rate_prerequisites, check_rate_services


class TestRateLimitServices:
    """Validate rate limit storage detection and prerequisites."""

    def test_returns_config_uri(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Use configured storage URI when provided."""

        # Provide a custom storage URI via configuration helper.
        monkeypatch.setattr(
            "flarchitect.utils.general.get_config_or_model_meta",
            lambda key, default=None, model=None: "redis://127.0.0.1:6379",
        )
        monkeypatch.setattr(
            "flarchitect.utils.general.check_rate_prerequisites",
            lambda service: None,
        )

        assert check_rate_services() == "redis://127.0.0.1:6379"

    def test_returns_none_without_services(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Return ``None`` when no cache services are reachable."""

        monkeypatch.setattr(
            "flarchitect.utils.general.get_config_or_model_meta",
            lambda key, default=None, model=None: None,
        )

        class DummySocket:
            def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - simple init
                """Placeholder socket that always fails to connect."""

            def settimeout(self, value: float) -> None:  # pragma: no cover
                pass

            def connect(self, address: tuple[str, int]) -> None:
                raise OSError

            def close(self) -> None:  # pragma: no cover
                pass

        monkeypatch.setattr(
            "flarchitect.utils.general.socket.socket", lambda *a, **k: DummySocket()
        )

        assert check_rate_services() is None

    def test_prerequisites_missing_dependency(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Raise ``ImportError`` if required client library is absent."""

        monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
        with pytest.raises(ImportError):
            check_rate_prerequisites("Redis")

    def test_invalid_storage_uri_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Unsupported URI schemes raise a ``ValueError``."""

        monkeypatch.setattr(
            "flarchitect.utils.general.get_config_or_model_meta",
            lambda key, default=None, model=None: "invalid://localhost",
        )
        with pytest.raises(ValueError):
            check_rate_services()

    def test_missing_host_in_storage_uri_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A storage URI without a host should raise ``ValueError``."""

        monkeypatch.setattr(
            "flarchitect.utils.general.get_config_or_model_meta",
            lambda key, default=None, model=None: "redis://",
        )
        with pytest.raises(ValueError):
            check_rate_services()
