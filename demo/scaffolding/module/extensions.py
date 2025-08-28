"""Extension instances for the scaffolding application."""

from __future__ import annotations

import datetime
from typing import Any

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect


class BaseModel(DeclarativeBase):
    """Base model with timestamp and soft delete support."""

    created: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    updated: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def get_session(*_args: Any, **_kwargs: Any):
        """Return the current database session."""

        return db.session


# Instantiate extensions globally to be initialised in the app factory.
db = SQLAlchemy(model_class=BaseModel)
schema = Architect()

__all__ = ["db", "schema", "BaseModel"]
