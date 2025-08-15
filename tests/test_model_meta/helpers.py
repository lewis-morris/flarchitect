import random
from datetime import datetime, timedelta

import numpy as np

from demo.model_extension.model.models import Author, Book, Category, Publisher, Review

categories = {
    "Fantasy": "Features magical elements, mythical creatures, and imaginary worlds.",
    "Science Fiction": "Explores futuristic concepts, advanced technology, and often space exploration.",
    "Mystery": "Involves suspenseful and puzzling scenarios, often with a detective or investigator.",
    "Thriller": "Focuses on generating excitement and suspense, with high stakes and constant tension.",
    "Romance": "Centres on love stories and romantic relationships between characters.",
    "Historical Fiction": "Set in the past, blending historical facts with fictional characters and plots.",
    "Horror": "Aimed to scare, unsettle, or horrify the reader, often with supernatural elements.",
    "Literary Fiction": "Emphasises themes, character development, and stylistic complexity over plot.",
    "Young Adult": "Targets teenagers and young adults, dealing with themes relevant to youth.",
    "Children's Books": "Designed for young readers, featuring stories and illustrations suitable for children.",
    "Biography": "A detailed account of a person's life, told by someone else.",
    "Self-Help": "Intended to guide readers in personal improvement and tackling personal problems.",
    "Cookbooks": "A collection of recipes and cooking tips, often accompanied by culinary guidance.",
    "Poetry": "Expressive writing, often employing verse, metre, and imagery for emotional impact.",
    "Graphic Novels": "Narrative works in which the story is conveyed through sequential art.",
}

good_words = [
    "amazing",
    "wonderful",
    "exciting",
    "delightful",
    "marvellous",
    "superb",
    "enjoyable",
    "splendid",
    "fabulous",
    "terrific",
    "entertaining",
    "joyful",
    "brilliant",
    "captivating",
    "magnificent",
]

bad_words = [
    "bad",
    "terrible",
    "awful",
    "boring",
    "unpleasant",
    "dreadful",
    "poor",
    "unenjoyable",
    "dismal",
    "mediocre",
    "horrible",
    "tedious",
    "miserable",
    "lacklustre",
    "uninspiring",
    "disappointing",
]

first_names = [
    "William",
    "James",
    "George",
    "Edward",
    "Charles",
    "Henry",
    "Robert",
    "John",
    "Thomas",
    "Richard",
    "David",
    "Michael",
    "Peter",
    "Christopher",
    "Benjamin",
    "Daniel",
    "Matthew",
    "Andrew",
    "Joseph",
    "Arthur",
    "Elizabeth",
    "Mary",
    "Margaret",
    "Catherine",
    "Jane",
    "Anne",
    "Victoria",
    "Sarah",
    "Emily",
    "Charlotte",
    "Emma",
    "Alice",
    "Helen",
    "Lucy",
    "Eleanor",
    "Grace",
    "Rebecca",
    "Abigail",
    "Olivia",
    "Sophia",
]

last_names = [
    "Smith",
    "Jones",
    "Taylor",
    "Brown",
    "Wilson",
    "Evans",
    "Thomas",
    "Roberts",
    "Johnson",
    "Lewis",
    "Morris",
    "Hughes",
    "Edwards",
    "Davies",
    "Williams",
    "Patel",
    "Jackson",
    "Lee",
    "Walker",
    "Robinson",
    "Wood",
    "Thompson",
    "White",
    "Watson",
    "Jackson",
    "Wright",
    "Green",
    "Harris",
    "Cooper",
    "King",
    "Edwards",
    "Clarke",
    "Turner",
]

nationality = ["English"] * 10 + ["Scottish"] * 10 + ["Welsh"] * 10 + ["Irish"] * 5 + ["American"] * 3 + ["Australian"] * 3

bios = [
    "Renowned for their vivid storytelling, this author has captivated readers worldwide with their imaginative narratives.",
    "With a unique voice that resonates across genres, this writer has consistently been at the forefront of literary innovation.",
    "An acclaimed master of character development, their books offer deep insights into the human condition.",
    "Known for their suspenseful plots and unexpected twists, this author has become a staple for thrill-seekers and mystery lovers alike.",
    "Their elegant prose and poetic descriptions have earned them a distinguished place among contemporary literary figures.",
    "With a keen eye for detail, this writer crafts immersive worlds that transport readers to different times and places.",
    "A trailblazer in their genre, they have garnered numerous awards and accolades for their groundbreaking work.",
    "Their compelling narratives and complex characters reflect a profound understanding of social and cultural dynamics.",
    "This author's ability to weave humour and wit into their storytelling has delighted audiences, making their books a joy to read.",
    "A champion of exploring challenging themes, their works are known for their depth and thought-provoking content.",
    "Blending rich imagination with intricate plots, this author creates captivating tales that linger in the minds of readers.",
    "Known for their eloquent narrative style, their books explore the nuances of everyday life with grace and sensitivity.",
    "With a flair for bringing characters to life, their stories resonate with readers, evoking a range of emotions.",
    "Their work stands out for its lyrical quality, turning even the most mundane scenarios into something magical.",
    "Masterfully constructing complex relationships in their narratives, this writer reveals the multifaceted nature of human connections.",
    "Renowned for crafting compelling dialogues, they bring authenticity and depth to each character they create.",
    "Their storytelling transcends boundaries, appealing to a diverse and broad audience with its universal themes.",
    "Expertly intertwining multiple storylines, they create rich tapestries that capture the complexity of life.",
    "Their attention to emotional detail makes each novel a deeply moving experience, inviting readers to reflect on their own lives.",
    "With a gift for observation, their books offer insightful perspectives on everyday experiences and encounters.",
]

recommendations = [
    "Definitely worth checking out!",
    "Highly recommended!",
    "I strongly suggest giving it a try.",
    "It's a must-see!",
    "You won't be disappointed.",
    "An absolute gem!",
    "Thoroughly enjoyable from start to finish.",
    "I can't recommend it enough!",
    "It exceeded my expectations.",
    "Truly outstanding in every way.",
    "A delightful experience that shouldn't be missed.",
    "It's been a long time since I've been this impressed.",
    "An exemplary showcase of quality.",
    "A perfect example of excellence.",
    "It's a standout choice in its category.",
]

negative_reviews = [
    "Utterly disappointing.",
    "I wouldn't recommend it at all.",
    "A complete waste of time.",
    "Far below expectations.",
    "Not worth the effort.",
    "Highly unsatisfactory.",
    "Left a lot to be desired.",
    "Thoroughly unenjoyable from start to finish.",
    "One of the worst I've experienced.",
    "Deeply regrettable.",
    "Falls short in every aspect.",
    "A dismal failure by all standards.",
    "An experience I'd like to forget.",
    "Missed the mark entirely.",
    "A letdown in every sense of the word.",
]


def make_isbn() -> str:
    """
    Generates a random ISBN number.
    Returns:
        str: Random ISBN number.
    """
    return "978" + str(random.randint(1000000, 9999999))


def generate_title() -> str:
    """
    Generates a random book title.
    Returns:
        str: Random book title.
    """
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
    """
    Generates a random company name.
    Returns:
        str: Random company name.
    """
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


def generate_random_year(start: int = 1860, end: int | None = None) -> int:
    """Generate a random year between ``start`` and ``end``.

    Args:
        start: The minimum year to generate.
        end: The maximum year to generate. Defaults to current year if ``None``.

    Returns:
        Randomly selected year within the given range.
    """

    if end is None:
        end = datetime.now().year
    return random.randint(start, end)


def random_ratings():
    """
    Generates a list of random ratings based on a normal distribution.
    Returns:
        list: List of random ratings.
    """
    # Parameters
    average_rating = random.randint(10, 90) / 10  # Desired average rating
    num_ratings = random.randint(30, 150)  # Total number of ratings
    std_dev = random.randint(5, 20) / 10

    # Generate ratings
    ratings = np.random.normal(average_rating, std_dev, num_ratings)

    # Scale ratings to be within 1-10
    ratings = np.clip(ratings, 1, 10)

    # Adjust to match the desired average more closely
    diff = average_rating - np.mean(ratings)
    ratings = np.clip(ratings + diff, 1, 10)

    # Check if within acceptable tolerance (e.g., 0.1)
    tolerance = 0.1
    if abs(np.mean(ratings) - average_rating) > tolerance:
        # Adjust if outside tolerance
        ratings = np.clip(ratings + (average_rating - np.mean(ratings)), 1, 10)

    # Convert to a list and round to nearest integer (optional)
    return [round(rating) for rating in ratings]


def load_dummy_database(db):
    """
    Loads dummy data into the database.
    """
    categories = create_categories(db)
    publishers = create_publishers(db)
    authors = create_authors(db)
    books = create_books(db, authors, categories, publishers)
    create_reviews(db, books)


def create_reviews(db, books):
    """
    Creates reviews in the database.

    Args:
        db (SQLAlchemy): SQLAlchemy database instance.
        books (list[Book]): List of books to choose from.

    Returns:
        None

    """

    for book in books:
        ratings = random_ratings()
        for rating in ratings:
            if rating >= 5:
                review_text = f"{book.author.full_name} has done an {random.choice(good_words)} job with this book. {random.choice(recommendations)}"
            else:
                review_text = f"{book.author.full_name} has done an {random.choice(good_words)} job with this book. {negative_reviews}"

            review = Review(
                rating=rating,
                book=book,
                review_text=review_text,
                book_id=book.id,
                reviewer_name=" ".join(get_name()),
            )
            db.session.add(review)
    db.session.commit()


def create_books(db, authors, categories, publishers):
    """
    Creates books in the database.

    Args:
        db (SQLAlchemy): SQLAlchemy database instance.
        categories (list[Category]): List of categories to choose from.
        authors (list[Author]): List of authors to choose from.

    Returns:
        list[Book]: List of books created.

    """

    books = []

    for author in authors:
        author_categories = []
        publisher = random.choice(publishers)
        for _ in range(random.randint(1, 3)):
            author_categories.append(random.choice(categories))
            author_categories = list(set(author_categories))

        for _ in range(3, 5):
            categories = random.choices(author_categories)
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
                categories=categories,
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
                    categories=categories,
                )
                db.session.add(book)
                books.append(book)

    db.session.commit()

    return books


def create_categories(db):
    """
    Creates categories in the database.

    Args:
        db (SQLAlchemy): SQLAlchemy database instance.

    Returns:
        list[Category]: List of categories created.

    """

    final_categories = []

    for k, v in categories.items():
        cat = Category(name=k, description=v)
        final_categories.append(cat)
        db.session.add(cat)

    db.session.commit()
    return final_categories


def create_publishers(db):
    """
        Creates publishers in the database.

    Args:
        db (SQLAlchemy): SQLAlchemy database instance.

    Returns:
        list[Publisher]: List of publishers created.

    """

    publishers = []

    for _ in range(30):
        name = generate_company_name()
        website = "https://" + name.replace(" ", "").replace("&", "and").lower() + ".co.uk"
        foundation_year = generate_random_year(1860, 1920)

        company = Publisher(name=name, website=website, foundation_year=foundation_year)
        publishers.append(company)
        db.session.add(company)

    db.session.commit()
    return publishers


def get_name():
    """
    Generates a random first and last name.
    Returns:
        tuple: First name and last name.
    """
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    return first_name, last_name


def create_authors(db):
    """
        Create Authors in the database.

    Args:
        db (SQLAlchemy): SQLAlchemy database instance.

    Returns:
        list[Author]: List of authors created.

    """

    authors = []

    for _ in range(60):
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
