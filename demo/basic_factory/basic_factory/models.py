from datetime import date, datetime

from sqlalchemy import (
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from demo.basic_factory.basic_factory.extensions import db

book_category_table = Table(
    "book_category",
    db.Model.metadata,
    Column("book_id", Integer, ForeignKey("books.id")),
    Column("category_id", Integer, ForeignKey("categories.id")),
)
book_category_table.Meta = {
    "tag_group": "Books",
    "tag": "Book Categories",
    "left_model": "Book",
    "right_model": "Category",
}


class Author(db.Model):
    __tablename__ = "authors"

    class Meta:
        # all models should have class Meta object and the following fields which defines how the model schema's are
        # references in redocly api docs.
        tag_group = "People/Companies"
        tag = "Author"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        info={"description": "The unique identifier for the author."},
    )
    first_name: Mapped[str] = mapped_column(String, info={"description": "The author's name", "format": "name"})
    last_name: Mapped[str] = mapped_column(String)
    biography: Mapped[str] = mapped_column(Text)
    date_of_birth: Mapped[datetime] = mapped_column(Date)
    nationality: Mapped[str] = mapped_column(String)
    website: Mapped[str | None] = mapped_column(String)
    books = relationship("Book", back_populates="author")

    @hybrid_property
    def full_name(self) -> str:
        """
        Hybrid properties are picked up by flarchitect also.
        Returns:
            full name (str): The full name which is a concatenation of the first and last name.
        """
        return f"{self.first_name} {self.last_name}"

    # To use hybrid properties in API filters, you MUST define an expression for it.
    # This does not affect hybrid properties from being output in the API response.
    @full_name.expression
    def full_name(cls):
        """
        Expression for generating the full name in SQL queries.
        """
        return cls.first_name + " " + cls.last_name


class Book(db.Model):
    __tablename__ = "books"

    class Meta:
        # all models should have class Meta object and the following fields which defines how the model schema's are
        # references in redocly api docs.
        tag_group = "Books"
        tag = "Books"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String)
    isbn: Mapped[str] = mapped_column(String)
    publication_date: Mapped[date] = mapped_column(Date)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("authors.id"))
    publisher_id: Mapped[int] = mapped_column(Integer, ForeignKey("publishers.id"))
    author = relationship("Author", back_populates="books")
    publisher = relationship("Publisher", back_populates="books")
    reviews = relationship("Review", back_populates="book")
    categories = relationship("Category", secondary=book_category_table, back_populates="books")


class Publisher(db.Model):
    __tablename__ = "publishers"

    class Meta:
        # all models should have class Meta object and the following fields which defines how the model schema's are
        # references in redocly api docs.
        tag_group = "People/Companies"
        tag = "Publisher"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    website: Mapped[str] = mapped_column(String)
    foundation_year: Mapped[str] = mapped_column(Integer)
    books = relationship("Book", back_populates="publisher", uselist=True)


class Review(db.Model):
    __tablename__ = "reviews"

    class Meta:
        # all models should have class Meta object and the following fields which defines how the model schema's are
        # references in redocly api docs.
        tag_group = "Books"
        tag = "Reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.id"))
    reviewer_name: Mapped[str] = mapped_column(String)
    rating: Mapped[str] = mapped_column(Float)
    review_text: Mapped[str] = mapped_column(Text)
    book = relationship("Book", back_populates="reviews")


class Category(db.Model):
    __tablename__ = "categories"

    class Meta:
        # all models should have class Meta object and the following fields which defines how the model schema's are
        # references in redocly api docs.
        tag_group = "Books"
        tag = "Categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    books = relationship("Book", secondary=book_category_table, back_populates="categories")
