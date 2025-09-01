Config by Method Models
==============================

    Global < Model < **Model Method**

:bdg-dark-line:`Model Method`

These values are defined as Meta class attributes in your `SQLAlchemy`_ models and configure specific behaviour per
`HTTP method`_ for a specific model.

-  They should always be lowercase
-  They should always omit any ``API_`` prefix.
-  They should be prefixed with the HTTP method you want to configure, e.g. ``get_``, ``post_``, ``patch_``, ``delete_``

Values defined here will apply per model/HTTP method and cannot be overridden.

Example
--------------

.. code:: python

    class Author:
        __tablename__ = "author"
        class Meta:
            # shows this description for the `GET` endpoint in the documentation
            get_description = "Models an author of a book"
            # adds a rate limit of 10 per minute to the `POST` endpoint
            post_rate_limit = "10 per minute"
            # requires authentication for the `GET` endpoint
            get_authenticate = True
            # does not require authentication for the `POST` endpoint
            post_authenticate = False
            # does not require authentication for the `PATCH` endpoint
            patch_authenticate = False
