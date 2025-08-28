from datetime import date, datetime

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, Table, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from demo.model_extension.model.extensions import db

book_category_table = Table(
    "book_category",
    db.Model.metadata,
    Column("book_id", Integer, ForeignKey("books.id")),
    Column("category_id", Integer, ForeignKey("categories.id")),
)


class Author(db.Model):
    __tablename__ = "authors"

    class Meta:
        # all models should have class Meta object and the following fields which defines how the model schema's are
        # references in redocly api docs.
        tag_group = "People/Companies"
        tag = "Author"
        # `block_methods` stop api calls via these methods.
        block_methods = ["POST", "PATCH"]

    # column definitions with `info` field which is used to define the schema in redocly api docs.
    # The `info` field is a dictionary with the following keys:
    # - description: The description of the field.
    # - format: The format of the field.Can be one of the following:
    #       date – full-date notation as defined by RFC 3339, section 5.6, for example, 2017-07-21
    #       date-time – the date-time notation as defined by RFC 3339, section 5.6, for example, 2017-07-21T17:32:28Z
    #       password – a hint to UIs to mask the input
    #       byte – base64-encoded characters, for example, U3dhZ2dlciByb2Nrcw==
    #       binary – binary data, used to describe files
    #       email
    #       uuid
    #       uri
    #       hostname
    #       ipv4
    #       ipv6
    #       and others
    # - example: An example of the field.
    # - validaror: An example of the field.

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        info={
            "description": "The unique identifier for the author.",
            "format": "int32",
            "example": 1,
        },
    )

    email: Mapped[str | None] = mapped_column(
        String,
        info={
            "description": "The author's email",
            "format": "email",
            "validator": "email",
        },
    )

    first_name: Mapped[str] = mapped_column(
        String,
        info={"description": "The author's name", "format": "text", "example": "John"},
    )

    last_name: Mapped[str] = mapped_column(
        String,
        info={
            "description": "The author's last name",
            "format": "text",
            "example": "Doe",
        },
    )

    biography: Mapped[str] = mapped_column(
        Text,
        info={
            "description": "The author's biography",
            "format": "text",
            "example": "John Doe is a prolific author.",
        },
    )

    date_of_birth: Mapped[datetime] = mapped_column(
        Date,
        info={
            "description": "The author's date of birth",
            "format": "date",
            "example": "1970-01-01",
        },
    )

    nationality: Mapped[str] = mapped_column(
        String,
        info={
            "description": "The author's nationality",
            "format": "text",
            "example": "English",
        },
    )

    website: Mapped[str | None] = mapped_column(
        String,
        info={
            "description": "The author's website",
            "format": "uri",
            "example": "https://www.johndoe.com",
        },
    )

    books = relationship("Book", back_populates="author")

    # By default, any field starting with an underscore is ignored by flarchitect. To change this behaviour, set the
    # `API_IGNORE_UNDERSCORE_ATTRIBUTES` to `False` in the app's configuration.
    _hidden_field: Mapped[str | None] = mapped_column(
        String,
        info={
            "description": "Hidden field",
            "format": "text",
            "example": "You should not see me",
        },
    )

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
        allowed_methods = ["GET", "POST", "PATCH"]

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    website: Mapped[str] = mapped_column(String, info={"format": "uri"})
    email: Mapped[str | None] = mapped_column(
        String,
        info={
            "description": "The author's email",
            "format": "email",
            "validator": "email",
            "validator_message": "Invalid email",
        },
    )
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
        allowed_methods = ["POST", "PATCH"]

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    books = relationship("Book", secondary=book_category_table, back_populates="categories")


class APICalls(db.Model):
    __tablename__ = "api_calls"

    class Meta:
        # all models should have class Meta object and the following fields which defines how the model schema's are
        # references in redocly api docs.
        tag_group = "Stats"
        tag = "APICalls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    endpoint: Mapped[str] = mapped_column(String)
    args: Mapped[str | None] = mapped_column(String)
    method: Mapped[str] = mapped_column(String)
    ip: Mapped[str | None] = mapped_column(String)
