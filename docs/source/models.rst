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

``flarchitect`` can serialize model responses in different formats, controlled
by ``API_SERIALIZATION_TYPE`` or ``Meta.serialization_type``. Supported dump
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
