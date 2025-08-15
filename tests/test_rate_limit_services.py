"""Tests for rate limit service utilities."""

from __future__ import annotations

import pytest

from flarchitect.utils.general import check_rate_prerequisites, check_rate_services


class TestRateLimitServices:
    """Validate rate limit storage detection and prerequisites."""

    def test_returns_config_uri(self) -> None:
        """Use configured storage URI when provided."""

        assert (
            check_rate_services(
                config_getter=lambda *_, **__: "redis://127.0.0.1:6379",
                prereq_checker=lambda _: None,
            )
            == "redis://127.0.0.1:6379"
        )

    def test_memory_storage_uri_allowed(self) -> None:
        """``memory://`` URIs do not require a host and should be accepted."""

        assert (
            check_rate_services(config_getter=lambda *_, **__: "memory://")
            == "memory://"
        )

    def test_returns_none_without_services(self) -> None:
        """Return ``None`` when no cache services are reachable."""

        class DummySocket:
            def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - simple init
                """Placeholder socket that always fails to connect."""

            def settimeout(self, value: float) -> None:  # pragma: no cover
                pass

            def connect(self, address: tuple[str, int]) -> None:
                raise OSError

            def close(self) -> None:  # pragma: no cover
                pass

        assert (
            check_rate_services(
                config_getter=lambda *_, **__: None,
                socket_factory=lambda *_, **__: DummySocket(),
            )
            is None
        )

    def test_prerequisites_missing_dependency(self) -> None:
        """Raise ``ImportError`` if required client library is absent."""

        with pytest.raises(ImportError):
            check_rate_prerequisites("Redis", find_spec=lambda name: None)

    def test_invalid_storage_uri_raises(self) -> None:
        """Unsupported URI schemes raise a ``ValueError``."""

        with pytest.raises(ValueError):
            check_rate_services(
                config_getter=lambda *_, **__: "invalid://localhost",
            )

    def test_missing_host_in_storage_uri_raises(self) -> None:
        """A storage URI without a host should raise ``ValueError``."""

        with pytest.raises(ValueError):
            check_rate_services(
                config_getter=lambda *_, **__: "redis://",
            )
