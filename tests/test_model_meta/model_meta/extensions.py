from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect


class BaseModel(DeclarativeBase):
    # you can optionally add fields that apply to all models.
    created: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_session(*args):
        # you must add a method to your base model called get session that returns a sqlalchemy session for the
        # auto api creator to work.
        return db.session


db = SQLAlchemy(model_class=BaseModel)
schema = Architect()
