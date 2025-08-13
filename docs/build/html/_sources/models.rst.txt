SQLAlchemy Models
=========================================

``flarchitect`` builds APIs directly from your SQLAlchemy models. To expose a model:

* Inherit from your configured base model.
* Add a ``Meta`` inner class with at least ``tag`` and ``tag_group`` attributes for documentation grouping.
* Define your fields and relationships as you normally would; nested relationships are handled automatically.

Example::

    class Author(BaseModel):
        __tablename__ = "author"

        class Meta:
            tag = "Author"
            tag_group = "People/Companies"

        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(80))

That's all that's required to make the model available through the generated API.

Nested model creation
---------------------

Nested writes are disabled by default. Enable them globally with
``API_ALLOW_NESTED_WRITES = True`` or per model via ``Meta.allow_nested_writes``.
Once enabled, ``AutoSchema`` can deserialize nested relationship data during
POST or PUT requests. Include related objects under the relationship name in
your payload::

    {
        "title": "My Book",
        "isbn": "12345",
        "publication_date": "2024-01-01",
        "author_id": 1,
        "author": {
            "first_name": "John",
            "last_name": "Doe",
            "biography": "Bio",
            "date_of_birth": "1980-01-01",
            "nationality": "US"
        }
    }

The nested ``author`` object is deserialized into an ``Author`` instance while
responses continue to use the configured serialization type (URL, JSON, or
dynamic).
