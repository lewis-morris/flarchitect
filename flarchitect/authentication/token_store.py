"""Persistent refresh token storage utilities.

This module defines a thread-safe API for persisting JWT refresh tokens
with their associated metadata. Tokens are stored in a database table
using SQLAlchemy, allowing the application to invalidate refresh tokens
and track their expiration.
"""

from __future__ import annotations

import datetime
from contextlib import AbstractContextManager, closing
from threading import Lock

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

from flarchitect.utils.session import _resolve_session


class Base(DeclarativeBase):
    """Base declarative class for refresh token models."""


class RefreshToken(Base):
    """SQLAlchemy model representing a stored refresh token."""

    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(String, primary_key=True)
    user_pk: Mapped[str] = mapped_column(String, nullable=False)
    user_lookup: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.datetime.now(datetime.timezone.utc))
    last_used_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revoked_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by: Mapped[str | None] = mapped_column(String, nullable=True)


_lock = Lock()


def _ensure_table(session: Session) -> None:
    """Create the refresh token table if it does not exist."""
    RefreshToken.metadata.create_all(bind=session.get_bind())


def _managed_session() -> AbstractContextManager[Session]:
    """Return a context manager that ensures the session is closed.

    Uses :func:`get_session` which isolates the global Flask-SQLAlchemy session
    when present, and otherwise manages the provided session directly.
    """
    session_or_ctx = get_session(RefreshToken)
    # If a contextmanager was returned, use it directly; else wrap in closing()
    if hasattr(session_or_ctx, "__enter__") and hasattr(session_or_ctx, "__exit__"):
        return session_or_ctx  # type: ignore[return-value]
    return closing(session_or_ctx)


def get_session(model: type[DeclarativeBase] | None = None):
    """Resolve a session suitable for token operations.

    If the active session is a Flask-SQLAlchemy scoped session, return a
    short-lived session bound to the same engine so closing does not impact
    the application session. Otherwise, wrap the resolved session for closing.
    """
    base_session = _resolve_session(model)
    is_scoped = hasattr(base_session, "remove") and hasattr(base_session, "registry")
    if is_scoped:
        bind = base_session.get_bind()
        SessionMaker = sessionmaker(bind=bind)
        return closing(SessionMaker())
    return closing(base_session)


def store_refresh_token(token: str, user_pk: str, user_lookup: str, expires_at: datetime.datetime) -> None:
    """Persist a refresh token and its metadata.

    Args:
        token: Encoded refresh token string.
        user_pk: User primary key value as a string.
        user_lookup: User lookup field value as a string.
        expires_at: Token expiration timestamp.
    """

    with _lock, _managed_session() as session:
        _ensure_table(session)
        session.merge(
            RefreshToken(
                token=token,
                user_pk=user_pk,
                user_lookup=user_lookup,
                expires_at=expires_at,
                created_at=datetime.datetime.now(datetime.timezone.utc),
                revoked=False,
            )
        )
        session.commit()


def get_refresh_token(token: str) -> RefreshToken | None:
    """Retrieve a stored refresh token.

    Args:
        token: Encoded refresh token string.

    Returns:
        RefreshToken | None: Stored refresh token or ``None`` if not found.
    """

    with _managed_session() as session:
        _ensure_table(session)
        session.expire_all()
        result = session.get(RefreshToken, token)
        # Hide revoked tokens from normal retrieval
        if result is not None and result.revoked:
            return None
    return result


def delete_refresh_token(token: str) -> None:
    """Remove a refresh token from storage in a thread-safe manner.

    Args:
        token: Encoded refresh token string.
    """

    with _lock, _managed_session() as session:
        _ensure_table(session)
        instance = session.get(RefreshToken, token)
        if instance is not None:
            session.delete(instance)
            session.commit()
            session.expire_all()


def revoke_refresh_token(token: str) -> None:
    """Mark a refresh token as revoked.

    This function preserves the row for auditing instead of deleting it.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    with _lock, _managed_session() as session:
        _ensure_table(session)
        instance = session.get(RefreshToken, token)
        if instance is not None:
            instance.revoked = True
            instance.revoked_at = now
            session.add(instance)
            session.commit()
            session.expire_all()


def mark_refresh_token_used(token: str, *, replaced_by: str | None = None) -> None:
    """Update auditing fields when a refresh token is used.

    Args:
        token: The refresh token being used.
        replaced_by: Optional new refresh token string created via rotation.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    with _lock, _managed_session() as session:
        _ensure_table(session)
        instance = session.get(RefreshToken, token)
        if instance is not None:
            instance.last_used_at = now
            if replaced_by:
                instance.replaced_by = replaced_by
            session.add(instance)
            session.commit()
            session.expire_all()


def rotate_refresh_token(old_token: str, new_token: str) -> None:
    """Rotate a refresh token by revoking the old and linking to the new.

    Sets ``last_used_at`` and ``replaced_by`` on the old token and marks it revoked.
    """
    mark_refresh_token_used(old_token, replaced_by=new_token)
    revoke_refresh_token(old_token)
