from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect


def _utc_naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class BaseModel(DeclarativeBase):
    # you can optionally add fields that apply to all models.
    created: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=_utc_naive_now)
    updated: Mapped[datetime] = mapped_column(DateTime, default=_utc_naive_now, onupdate=_utc_naive_now)
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    def get_session(*args):
        # you must add a method to your base model called get session that returns a sqlalchemy session for the
        # auto api creator to work.
        return db.session


db = SQLAlchemy(model_class=BaseModel)
schema = Architect()
