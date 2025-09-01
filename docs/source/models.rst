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

Dump types
----------

``flarchitect`` can serialise model responses in different formats, controlled
by `API_SERIALIZATION_TYPE <configuration.html#SERIALIZATION_TYPE>`_ or ``Meta.serialization_type``. Supported dump
types are:

* ``url`` (default) – represent related objects only by their URL links.
* ``json`` – embed related objects as JSON objects.
* ``dynamic`` – choose between ``url`` and ``json`` using the ``dump`` query
  parameter.
* ``hybrid`` – include both URL links and embedded JSON for related objects.

Example::

    class Config:
        API_SERIALIZATION_TYPE = "json"

Clients can override ``dynamic`` dumps per request with
``?dump=url`` or ``?dump=json``.

Nested relationship dumping
---------------------------

`API_ADD_RELATIONS <configuration.html#ADD_RELATIONS>`_ controls whether relationship fields are included in the
serialised response. Disable it to return only column data, or use
``?dump_relationships=false`` on a request to temporarily suppress all
relationships.

`API_SERIALIZATION_DEPTH <configuration.html#SERIALIZATION_DEPTH>`_ limits how many levels of related resources are
embedded. Increasing the depth exposes deeper links or objects but may add
overhead.

For `API_SERIALIZATION_TYPE <configuration.html#SERIALIZATION_TYPE>`_ set to ``"dynamic"``, clients can choose which
relationships to embed by supplying a comma-separated ``join`` parameter, e.g.
``?join=books,publisher``. Any relationships not listed are returned as URLs.

Example responses
^^^^^^^^^^^^^^^^^

URL-only dump (depth ``1``)::

    GET /api/authors/1
    {
        "id": 1,
        "name": "Alice",
        "books": "/api/authors/1/books"
    }

JSON dump (depth ``1``)::

    GET /api/authors/1?dump=json
    {
        "id": 1,
        "name": "Alice",
        "books": [
            {"id": 10, "title": "Example", "publisher": "/api/publishers/5"}
        ]
    }

JSON dump (depth ``2`` with `API_SERIALIZATION_DEPTH <configuration.html#SERIALIZATION_DEPTH>`_ = ``2`` or ``?join=books,publisher``)::

    GET /api/authors/1?dump=json
    {
        "id": 1,
        "name": "Alice",
        "books": [
            {"id": 10, "title": "Example", "publisher": {"id": 5, "name": "ACME"}}
        ]
    }

Hybrid dump::

    GET /api/authors/1?dump=hybrid
    {
        "id": 1,
        "name": "Alice",
        "books": "/api/authors/1/books",
        "publisher": {"id": 5, "name": "ACME"}
    }
