"""Run this module to start a tiny GraphQL server powered by flarchitect."""

from __future__ import annotations

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from flarchitect import Architect
from flarchitect.graphql import create_schema_from_models


class BaseModel(DeclarativeBase):
    """Base model for the demo."""


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
app.config["API_TITLE"] = "GraphQL Demo"
app.config["API_VERSION"] = "1.0"
app.config["API_BASE_MODEL"] = BaseModel

db = SQLAlchemy(model_class=BaseModel)


class Item(db.Model):
    """Simple item model exposed via GraphQL."""

    __tablename__ = "item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)


with app.app_context():
    db.init_app(app)
    db.create_all()
    architect = Architect(app)
    schema = create_schema_from_models([Item], db.session)
    architect.init_graphql(schema=schema)

if __name__ == "__main__":
    app.run(debug=True)
