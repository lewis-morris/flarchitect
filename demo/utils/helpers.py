"""Helper functions for generating demo data."""

import random
from datetime import datetime, timedelta

import numpy as np

from demo.basic_factory.basic_factory.models import (
    Author,
    Book,
    Category,
    Publisher,
    Review,
)
from demo.utils.constants import (
    bad_words,
    bios,
    categories,
    first_names,
    good_words,
    last_names,
    nationality,
    negative_reviews,
    recommendations,
)


def make_isbn() -> str:
    """Generate a random ISBN number."""
    return "978" + str(random.randint(1000000, 9999999))


def generate_title() -> str:
    """Generate a random book title."""
    # Title patterns
    patterns = [
        "The [adj] [noun]",
        "[adj] [noun] of [theme]",
        "[noun]'s [theme]",
        "The [noun] of the [theme]",
        "[theme] in the [noun]",
    ]

    adjectives = [
        "Lost",
        "Eternal",
        "Mysterious",
        "Forgotten",
        "Hidden",
        "Ancient",
        "Forbidden",
        "Whispering",
        "Shattered",
        "Enchanted",
        "Silent",
        "Distant",
        "Haunting",
        "Unspoken",
        "Celestial",
        "Crimson",
        "Wandering",
        "Serene",
        "Twilight",
        "Fading",
    ]

    nouns = [
        "Garden",
        "Secret",
        "Shadow",
        "Journey",
        "Echo",
        "Fortress",
        "River",
        "Dream",
        "Flame",
        "Horizon",
        "Labyrinth",
        "Chronicle",
        "Citadel",
        "Oasis",
        "Abyss",
        "Summit",
        "Void",
        "Beacon",
        "Mirage",
        "Tempest",
    ]

    themes = [
        "Love",
        "Betrayal",
        "Courage",
        "Adventure",
        "Truth",
        "Destiny",
        "Freedom",
        "Power",
        "Redemption",
        "Mystery",
        "Fate",
        "Harmony",
        "Wrath",
        "Solitude",
        "Illusion",
        "Legacy",
        "Sacrifice",
        "Victory",
        "Despair",
        "Hope",
    ]

    pattern = random.choice(patterns)
    adj = random.choice(adjectives)
    noun = random.choice(nouns)
    theme = random.choice(themes)

    # Replace placeholders with actual words
    title = pattern.replace("[adj]", adj).replace("[noun]", noun).replace("[theme]", theme)

    return title


# Words related to publishing and printing


def generate_company_name() -> str:
    """Generate a random company name."""
    nouns = [
        "Page",
        "Ink",
        "Quill",
        "Script",
        "Scroll",
        "Book",
        "Chapter",
        "Story",
        "Tale",
        "Verse",
    ]
    adjectives = [
        "Creative",
        "Boundless",
        "Epic",
        "Classic",
        "Timeless",
        "Innovative",
        "Digital",
        "Printed",
        "Prolific",
        "Inspired",
    ]
    suffixes = [
        "Publishing",
        "Press",
        "Printers",
        "Books",
        "Media",
        "House",
        "Group",
        "Studio",
        "Works",
        "Editions",
    ]

    noun = random.choice(nouns)
    noun_alt = random.choice(nouns)
    adjective = random.choice(adjectives)
    suffix = random.choice(suffixes)

    # Randomly choose a pattern
    patterns = [
        f"{noun} {suffix}",
        f"{adjective} {noun} {suffix}",
        f"The {adjective} {noun}",
        f"{noun} & {noun_alt} {suffix}",
    ]
    return random.choice(patterns)


def generate_random_year(start: int = 1860, to: int = datetime.now().year) -> int:
    """Generate a random year between ``start`` and ``to``."""
    return random.randint(start, to)


def random_ratings() -> list[int]:
    """Generate a list of random ratings based on a normal distribution."""
    average_rating = random.randint(10, 90) / 10
    num_ratings = random.randint(30, 150)
    std_dev = random.randint(5, 20) / 10

    ratings = np.random.normal(average_rating, std_dev, num_ratings)
    ratings = np.clip(ratings, 1, 10)

    diff = average_rating - np.mean(ratings)
    ratings = np.clip(ratings + diff, 1, 10)

    tolerance = 0.1
    if abs(np.mean(ratings) - average_rating) > tolerance:
        ratings = np.clip(ratings + (average_rating - np.mean(ratings)), 1, 10)

    return [round(rating) for rating in ratings]


def load_dummy_database(db):
    """Load dummy data into the database."""
    categories = create_categories(db)
    publishers = create_publishers(db)
    authors = create_authors(db)
    books = create_books(db, authors, categories, publishers)
    create_reviews(db, books)


def create_reviews(db, books):
    """Create reviews in the database."""
    for book in books:
        ratings = random_ratings()
        for rating in ratings:
            if rating >= 5:
                review_text = f"{book.author.full_name} has done an {random.choice(good_words)} job with this book. {random.choice(recommendations)}"
            else:
                review_text = f"{book.author.full_name} has done an {random.choice(bad_words)} job with this book. {random.choice(negative_reviews)}"

            review = Review(
                rating=rating,
                book=book,
                review_text=review_text,
                book_id=book.id,
                reviewer_name=" ".join(get_name()),
            )
            db.session.add(review)
    db.session.commit()


def create_books(
    db,
    authors: list[Author],
    categories: list[Category],
    publishers: list[Publisher],
) -> list[Book]:
    """Create books in the database."""
    books: list[Book] = []

    for author in authors:
        author_categories: list[Category] = []
        publisher = random.choice(publishers)
        for _ in range(0, random.randint(1, 3)):
            author_categories.append(random.choice(categories))
        author_categories = list(set(author_categories))

        for _ in range(3, 5):
            categories_for_book = random.choices(author_categories)
            isbn = make_isbn()
            title = generate_title()
            publication_year = generate_random_year(author.date_of_birth.year + 20, datetime.now().year)

            publication_date = datetime(
                year=publication_year,
                month=random.randint(1, 12),
                day=random.randint(1, 28),
            )

            book = Book(
                isbn=isbn,
                title=title,
                publication_date=publication_date,
                author=author,
                publisher=publisher,
                categories=categories_for_book,
            )
            db.session.add(book)
            books.append(book)

            if random.randint(1, 10) <= 2:
                pub_date = publication_date + timedelta(days=365 * random.randint(1, 4))
                book = Book(
                    isbn=isbn,
                    title=title + ": The Sequel",
                    publication_date=pub_date,
                    author=author,
                    publisher=publisher,
                    categories=categories_for_book,
                )
                db.session.add(book)
                books.append(book)

    db.session.commit()
    return books


def create_categories(db) -> list[Category]:
    """Create categories in the database."""
    final_categories: list[Category] = []
    for name, description in categories.items():
        cat = Category(name=name, description=description)
        final_categories.append(cat)
        db.session.add(cat)

    db.session.commit()
    return final_categories


def create_publishers(db) -> list[Publisher]:
    """Create publishers in the database."""
    publishers: list[Publisher] = []
    for _ in range(0, 30):
        name = generate_company_name()
        website = "https://" + name.replace(" ", "").replace("&", "and").lower() + ".co.uk"
        foundation_year = generate_random_year(1860, 1920)

        company = Publisher(name=name, website=website, foundation_year=foundation_year)
        publishers.append(company)
        db.session.add(company)

    db.session.commit()
    return publishers


def get_name() -> tuple[str, str]:
    """Generate a random first and last name."""
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    return first_name, last_name


def create_authors(db) -> list[Author]:
    """Create authors in the database."""
    authors: list[Author] = []

    for _ in range(0, 60):
        first_name, last_name = get_name()
        website = "https://" + (first_name + last_name).lower() + ".co.uk"
        rand_nationality = random.choice(nationality)
        year_born = datetime.now().year - 20
        date_of_birth = generate_random_year(1940, year_born)
        biography = f"""{first_name} is a {rand_nationality} writer born in {year_born}. {random.choice(bios)}"""

        author = Author(
            first_name=first_name,
            last_name=last_name,
            biography=biography,
            date_of_birth=datetime(
                year=date_of_birth,
                month=random.randint(1, 12),
                day=random.randint(1, 28),
            ),
            nationality=rand_nationality,
            website=website,
        )
        authors.append(author)
        db.session.add(author)

    db.session.commit()
    return authors
