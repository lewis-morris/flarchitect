"""Run a GraphQL server showcasing relationships and pagination."""

from __future__ import annotations

from datetime import datetime

import graphene
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from flarchitect import Architect
from flarchitect.graphql import SQLA_TYPE_MAPPING, create_schema_from_models


class BaseModel(DeclarativeBase):
    """Base model for the advanced demo."""


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
app.config["API_TITLE"] = "Advanced GraphQL Demo"
app.config["API_VERSION"] = "1.0"
app.config["API_BASE_MODEL"] = BaseModel

db = SQLAlchemy(model_class=BaseModel)


class Category(db.Model):
    """Category model with a relationship to ``Item``."""

    __tablename__ = "category"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    items: Mapped[list[Item]] = relationship(back_populates="category")


class Item(db.Model):
    """Item model demonstrating custom types and relationships."""

    __tablename__ = "item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    created: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"))
    category: Mapped[Category] = relationship(back_populates="items")


# Extend type mapping for ``DateTime`` columns.
SQLA_TYPE_MAPPING[DateTime] = graphene.DateTime

with app.app_context():
    db.init_app(app)
    db.create_all()
    schema = create_schema_from_models([Category, Item], db.session)

    class Query(schema.query):  # type: ignore[attr-defined]
        """Additional queries with filtering and pagination."""

        items_by_category = graphene.List(
            schema.get_type("ItemType"),  # type: ignore[attr-defined]
            category_id=graphene.Int(required=True),
            limit=graphene.Int(),
            offset=graphene.Int(),
        )

        @staticmethod
        def resolve_items_by_category(
            _root,
            _info,
            category_id: int,
            limit: int | None = None,
            offset: int | None = None,
        ):
            """Return items for a category with optional pagination."""

            query = db.session.query(Item).filter_by(category_id=category_id)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()

    class Mutation(schema.mutation):  # type: ignore[attr-defined]
        """Extend mutations with update and delete operations."""

        update_item = graphene.Field(
            schema.get_type("ItemType"),  # type: ignore[attr-defined]
            id=graphene.Int(required=True),
            name=graphene.String(),
        )
        delete_item = graphene.Boolean(id=graphene.Int(required=True))

        @staticmethod
        def resolve_update_item(_root, _info, id: int, name: str | None = None):
            """Update an item's fields and return the result."""

            item = db.session.get(Item, id)
            if item and name is not None:
                item.name = name
                db.session.commit()
            return item

        @staticmethod
        def resolve_delete_item(_root, _info, id: int) -> bool:
            """Delete an item by identifier."""

            item = db.session.get(Item, id)
            if not item:
                return False
            db.session.delete(item)
            db.session.commit()
            return True

    advanced_schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)

    architect = Architect(app)
    architect.init_graphql(schema=advanced_schema)

if __name__ == "__main__":
    app.run(debug=True)
