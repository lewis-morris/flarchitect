"""Tests for GraphQL integration."""

from __future__ import annotations

from collections.abc import Generator

import graphene
import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from flarchitect import Architect


class Base(DeclarativeBase):
    """Base declarative model used in tests."""


db = SQLAlchemy(model_class=Base)


class Author(db.Model):
    """Author model with a one-to-many relationship to books."""

    __tablename__ = "author"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    books: Mapped[list[Book]] = relationship("Book", back_populates="author")


class Book(db.Model):
    """Book model for GraphQL tests."""

    __tablename__ = "book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship("Author", back_populates="books")


class AuthorType(graphene.ObjectType):
    """GraphQL type exposing author fields and related books."""

    id = graphene.Int()
    name = graphene.String()
    books = graphene.List(lambda: BookType)

    def resolve_books(self, info: graphene.ResolveInfo) -> list[Book]:
        """Return books for the author."""

        return self.books


class BookType(graphene.ObjectType):
    """GraphQL type exposing book fields and its author."""

    id = graphene.Int()
    title = graphene.String()
    author = graphene.Field(AuthorType)

    def resolve_author(self, info: graphene.ResolveInfo) -> Author:
        """Return the book's author."""

        return self.author


class Query(graphene.ObjectType):
    """GraphQL query definitions."""

    book = graphene.Field(BookType, id=graphene.Int(required=True))
    all_books = graphene.List(
        BookType, title=graphene.String(), limit=graphene.Int(), offset=graphene.Int()
    )
    author = graphene.Field(AuthorType, id=graphene.Int(required=True))
    all_authors = graphene.List(AuthorType)

    def resolve_book(self, info: graphene.ResolveInfo, id: int) -> Book | None:
        """Return a book by its ID."""

        return db.session.get(Book, id)

    def resolve_all_books(
        self,
        info: graphene.ResolveInfo,
        title: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Book]:
        """Return books optionally filtered and paginated."""

        query = db.session.query(Book)
        if title:
            query = query.filter(Book.title == title)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()

    def resolve_author(self, info: graphene.ResolveInfo, id: int) -> Author | None:
        """Return an author by ID."""

        return db.session.get(Author, id)

    def resolve_all_authors(self, info: graphene.ResolveInfo) -> list[Author]:
        """Return all authors."""

        return db.session.query(Author).all()


class CreateBook(graphene.Mutation):
    """Mutation for creating books."""

    class Arguments:
        title = graphene.String(required=True)
        author_id = graphene.Int(required=True)

    Output = BookType

    @staticmethod
    def mutate(root, info: graphene.ResolveInfo, title: str, author_id: int) -> Book:
        """Create a new book."""

        book = Book(title=title, author_id=author_id)
        db.session.add(book)
        db.session.commit()
        return book


class UpdateBook(graphene.Mutation):
    """Mutation for updating book titles."""

    class Arguments:
        id = graphene.Int(required=True)
        title = graphene.String(required=True)

    Output = BookType

    @staticmethod
    def mutate(root, info: graphene.ResolveInfo, id: int, title: str) -> Book:
        """Update an existing book."""

        book = db.session.get(Book, id)
        if not book:
            raise Exception("Book not found")
        book.title = title
        db.session.commit()
        return book


class DeleteBook(graphene.Mutation):
    """Mutation for deleting books."""

    class Arguments:
        id = graphene.Int(required=True)

    ok = graphene.Boolean()

    @staticmethod
    def mutate(root, info: graphene.ResolveInfo, id: int) -> DeleteBook:
        """Delete a book by ID."""

        book = db.session.get(Book, id)
        if not book:
            raise Exception("Book not found")
        db.session.delete(book)
        db.session.commit()
        return DeleteBook(ok=True)


class Mutation(graphene.ObjectType):
    """GraphQL mutations."""

    create_book = CreateBook.Field()
    update_book = UpdateBook.Field()
    delete_book = DeleteBook.Field()


schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)


@pytest.fixture()
def app() -> Generator[Flask, None, None]:
    """Create a test app with GraphQL schema and seeded data."""

    app = Flask(__name__)
    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        API_TITLE="Test API",
        API_VERSION="1.0",
        API_BASE_MODEL=Base,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        author_one = Author(name="Author One")
        author_two = Author(name="Author Two")
        db.session.add_all(
            [
                author_one,
                author_two,
                Book(title="Book A1", author=author_one),
                Book(title="Book A2", author=author_one),
                Book(title="Book B1", author=author_two),
            ]
        )
        db.session.commit()
        arch = Architect(app)
        arch.init_graphql(schema=schema)
    yield app


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """Flask test client for GraphQL endpoint."""

    return app.test_client()


def test_book_mutations(client: FlaskClient) -> None:
    """Test create, update and delete mutations including failures."""

    mutation = {
        "query": 'mutation { create_book(title: "Book C1", author_id: 1) { id title } }'
    }
    response = client.post("/graphql", json=mutation)
    assert response.status_code == 200
    book_id = response.json["data"]["create_book"]["id"]
    assert response.json["data"]["create_book"]["title"] == "Book C1"

    mutation = {
        "query": f'mutation {{ update_book(id: {book_id}, title: "Book C1 Updated") {{ id title }} }}'
    }
    response = client.post("/graphql", json=mutation)
    assert response.status_code == 200
    assert response.json["data"]["update_book"]["title"] == "Book C1 Updated"

    mutation = {"query": 'mutation { update_book(id: 999, title: "Nope") { id } }'}
    response = client.post("/graphql", json=mutation)
    assert response.status_code == 200
    assert "errors" in response.json

    mutation = {"query": f"mutation {{ delete_book(id: {book_id}) {{ ok }} }}"}
    response = client.post("/graphql", json=mutation)
    assert response.status_code == 200
    assert response.json["data"]["delete_book"]["ok"] is True

    mutation = {"query": "mutation { delete_book(id: 999) { ok } }"}
    response = client.post("/graphql", json=mutation)
    assert response.status_code == 200
    assert "errors" in response.json


def test_filtering_and_pagination(client: FlaskClient) -> None:
    """Test filtering and pagination in queries."""

    query = {"query": '{ all_books(title: "Book A1") { title } }'}
    response = client.post("/graphql", json=query)
    assert response.status_code == 200
    assert response.json["data"]["all_books"] == [{"title": "Book A1"}]

    query = {"query": '{ all_books(title: "Missing") { title } }'}
    response = client.post("/graphql", json=query)
    assert response.status_code == 200
    assert response.json["data"]["all_books"] == []

    query = {"query": "{ all_books(limit: 2, offset: 1) { title } }"}
    response = client.post("/graphql", json=query)
    assert response.status_code == 200
    titles = [book["title"] for book in response.json["data"]["all_books"]]
    assert titles == ["Book A2", "Book B1"]

    query = {"query": "{ all_books(limit: 2, offset: 10) { title } }"}
    response = client.post("/graphql", json=query)
    assert response.status_code == 200
    assert response.json["data"]["all_books"] == []


def test_relationship_query(client: FlaskClient) -> None:
    """Ensure relationship queries return nested data."""

    query = {"query": "{ author(id: 1) { name books { title } } }"}
    response = client.post("/graphql", json=query)
    assert response.status_code == 200
    assert response.json["data"]["author"]["name"] == "Author One"
    book_titles = {book["title"] for book in response.json["data"]["author"]["books"]}
    assert book_titles == {"Book A1", "Book A2"}


def test_invalid_field_error(client: FlaskClient) -> None:
    """Requesting an unknown field should yield an error."""

    query = {"query": "{ all_books { unknown } }"}
    response = client.post("/graphql", json=query)
    assert response.status_code == 200
    assert "errors" in response.json
