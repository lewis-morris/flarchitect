Config Models
==============================

    Global < Global Method < **Model** < Model Method

:bdg-dark-line:`Model`

These values are defined as Meta class attributes in you `SQLAlchemy`_ models.

-  They should always be lowercase
-  They should always omit any ``API_`` prefix.

Values defined here will apply per model and can only be overridden by the a :bdg-dark-line:`Model Method` config
values.

Overrides :bdg-dark-line:`Global`, :bdg-dark-line:`Global Method`

Example
--------------

.. code:: python

    class Author():

        __table__ = "author"

        class Meta:
            # adds this model to the "People" tag group in the documentation
            tag_group = "People/Companies"
            # the name of this model in the docs
            group = "Author"
            # a description of this model applied to all endpoints for this model
            description = "Models an author of a book"
            # the rate limit across all HTTP methods for this model
            rate_limit = "10 per minute"
