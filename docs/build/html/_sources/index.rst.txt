flarchitect
=========================================

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   models
   authentication
   callbacks
   configuration
   faq
   genindex


keema-architect == bread, flarchitect.architect == api

.. image:: /_static/coverage.svg
   :alt: Coverage Report

.. image:: https://img.shields.io/github/license/arched-dev/flarchitect
   :alt: GitHub License

.. image:: https://img.shields.io/pypi/dm/flarchitect
   :alt: PyPI - Downloads

.. image:: https://badgen.net/static/Repo/Github/blue?icon=github&link=https%3A%2F%2Fgithub.com%2Farched-dev%2Fflarchitect
   :alt: GitHub Repo
   :target: https://github.com/arched-dev/flarchitect



--------------------------------------------



**flarchitect** automatically creates rapid, prototype or production ready API's directly from `SQLAlchemy`_ models with
accompanying `Redoc`_ documentation, all with little to no effort.

By adding **flarchitect** to your `Flask`_ application, you can be up and running in seconds, creating a fully functional
RESTful API, with a plethora of configuration options to suit your needs.

What can it do?

* Automatically detect and create endpoints, with nested model relationships and more.

* Standardize your API responses with a consistent format.

* Authenticate users with a variety of methods.

* Add ratelimiting, caching and more with no work.

* Be configured globally in `Flask`_ or in your `SQLAlchemy`_ models.

* Automatically generate `Redoc`_ documentation.

What are you waiting for...?

Turn this.

.. code:: python

    class Book(db.Model):

        id = db.Column(db.Integer, primary_key=True)
        title = db.Column(db.String(80), unique=True, nullable=False)
        author = db.Column(db.String(80), nullable=False)
        published = db.Column(db.DateTime, nullable=False)



Into this:

``GET /api/books``

.. code:: json

    {
      "datetime": "2024-01-01T00:00:00.0000+00:00",
      "api_version": "0.1.0",
      "status_code": 200,
      "response_ms": 15,
      "total_count": 10,
      "next_url": "/api/authors?limit=2&page=3",
      "previous_url": "/api/authors?limit=2&page=1",
      "error": "null",
      "value": [
        {
          "author": "John Doe",
          "id": 3,
          "published": "2024-01-01T00:00:00.0000+00:00",
          "title": "The Book"
        },
        {
          "author": "Jane Doe",
          "id": 4,
          "published": "2024-01-01T00:00:00.0000+00:00",
          "title": "The Book 2"
        }
      ]
    }

Let's get started!

:doc:`Quick Start <quickstart>`

`View Demos <https://github.com/arched-dev/flarchitect/tree/master/demo>`__


.. image:: /_static/one_does_not.png
   :alt: One does not simply generate API's
   :align: center
   :width: 100%
