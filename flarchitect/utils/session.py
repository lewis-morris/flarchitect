"""Utilities for resolving SQLAlchemy sessions.

This module provides :func:`get_session`, a helper that tries to
locate the active :class:`sqlalchemy.orm.Session` object used by the
application. It supports both ``Flask-SQLAlchemy`` and plain SQLAlchemy
setups so that models do not need to implement their own
``get_session`` method.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager, suppress
from typing import Any

from flask import current_app
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from flarchitect.utils.config_helpers import get_config_or_model_meta


def _session_from_config(model: type[DeclarativeBase] | None) -> Session | None:
    try:
        custom_getter: Callable[[], Session] | None = get_config_or_model_meta("API_SESSION_GETTER", model=model, default=None)
        if callable(custom_getter):
            session = custom_getter()
            if session is not None:
                return session
    except Exception:  # pragma: no cover - defensive
        pass
    return None


def _session_from_flask_extension() -> Session | None:
    try:  # pragma: no cover - only executed when Flask context exists
        ext = current_app.extensions.get("sqlalchemy")  # type: ignore[attr-defined]
        if ext is not None:
            session = getattr(ext, "session", None)
            if session is not None:
                return session
    except Exception:  # pragma: no cover - defensive
        pass
    return None


def _session_from_model_query(model: type[DeclarativeBase]) -> Session | None:
    query = getattr(model, "query", None)
    return getattr(query, "session", None)


def _session_from_legacy_getter(model: type[DeclarativeBase]) -> Session | None:
    legacy_getter = getattr(model, "get_session", None)
    if not callable(legacy_getter):
        return None
    session = legacy_getter()
    return session if session is not None else None


def _bound_engine(model: type[DeclarativeBase]) -> Any | None:
    table_metadata = getattr(getattr(model, "__table__", None), "metadata", None)
    engine = getattr(table_metadata, "bind", None)
    return engine if engine is not None else getattr(getattr(model, "metadata", None), "bind", None)


def _session_from_model_bind(model: type[DeclarativeBase]) -> Session | None:
    engine = _bound_engine(model)
    if engine is None:
        return None
    SessionMaker = sessionmaker(bind=engine)
    return SessionMaker()


def _model_session_candidates(model: type[DeclarativeBase]) -> tuple[Session | None, ...]:
    return (
        _session_from_model_query(model),
        _session_from_legacy_getter(model),
        _session_from_model_bind(model),
    )


def _resolve_session(model: type[DeclarativeBase] | None = None) -> Session:
    """Resolve an active SQLAlchemy session for the given model.

    This function contains the session resolution logic and is used internally
    by :func:`get_session`.

    Args:
        model: Optional SQLAlchemy declarative model used when searching for a
            session.

    Returns:
        Session: The resolved SQLAlchemy session instance.

    Raises:
        RuntimeError: If no session can be determined.
    """

    for session in (_session_from_config(model), _session_from_flask_extension()):
        if session is not None:
            return session

    if model is not None:
        for session in _model_session_candidates(model):
            if session is not None:
                return session

    raise RuntimeError("Unable to determine database session; configure API_SESSION_GETTER or bind an engine.")


@contextmanager
def get_session(model: type[DeclarativeBase] | None = None) -> Iterator[Session]:
    """Yield the active SQLAlchemy :class:`~sqlalchemy.orm.Session`.

    The session is resolved using :func:`_resolve_session` and is automatically
    closed when the context manager exits.

    Args:
        model: Optional SQLAlchemy declarative model used when searching for a
            session.

    Yields:
        Session: The resolved SQLAlchemy session instance.

    Raises:
        RuntimeError: If no session can be determined.
    """

    session = _resolve_session(model)
    try:
        yield session
    finally:
        with suppress(Exception):  # pragma: no cover - defensive
            session.close()
