flarchitect
=========================================

.. toctree::
   :hidden:
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   models
   validation
   authentication
   callbacks
   configuration
   advanced_configuration
   soft_delete
   openapi
   faq
   genindex

.. image:: /_static/coverage.svg
   :alt: Coverage Report

.. image:: https://github.com/lewis-morris/flarchitect/actions/workflows/run-unit-tests.yml/badge.svg?branch=master
   :alt: Tests

.. image:: https://img.shields.io/github/license/arched-dev/flarchitect
   :alt: GitHub License

.. image:: https://img.shields.io/pypi/dm/flarchitect
   :alt: PyPI - Downloads

.. image:: https://badgen.net/static/Repo/Github/blue?icon=github&link=https%3A%2F%2Fgithub.com%2Farched-dev%2Fflarchitect
   :alt: GitHub Repo
   :target: https://github.com/arched-dev/flarchitect



--------------------------------------------



**flarchitect** turns your `SQLAlchemy`_ models into a polished RESTful API complete with interactive `Redoc`_ or Swagger UI documentation.
Hook it into your `Flask`_ application and you'll have endpoints, schemas and docs in moments.

What can it do?

* Automatically detect and create endpoints, including nested relationships.
* Standardise responses with a consistent structure.
* Authenticate users with JWT access and refresh tokens.
* Add configurable rate limits backed by Redis, Memcached or MongoDB.
* Be configured globally in `Flask`_ or per model via ``Meta`` attributes.
* Generate `Redoc`_ or Swagger UI documentation on the fly.
* Extend behaviour with response callbacks, custom validators and per-route hooks (:ref:`advanced-callbacks`).

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
      "errors": null,
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

