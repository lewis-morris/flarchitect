flarchitect
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Getting Started
   :hidden:

   installation
   quickstart
   getting_started

.. toctree::
   :maxdepth: 2
   :caption: User Guide
   :hidden:

   models
   authentication
   validation
   callbacks
   openapi
   soft_delete
   configuration
   advanced_configuration
   faq
   roadmap

.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics
   :hidden:

   advanced_demo

.. image:: /_static/coverage.svg
   :alt: Coverage Report

.. image:: /_static/version.svg
   :alt: Package Version

.. image:: https://github.com/lewis-morris/flarchitect/actions/workflows/run-unit-tests.yml/badge.svg?branch=master
   :alt: Tests

.. image:: https://img.shields.io/pypi/v/flarchitect.svg
   :alt: PyPI Version
   :target: https://pypi.org/project/flarchitect/

.. image:: https://img.shields.io/github/license/lewis-morris/flarchitect
   :alt: GitHub License

.. image:: https://badgen.net/static/Repo/Github/blue?icon=github&link=https%3A%2F%2Fgithub.com%2Flewis-morris%2Fflarchitect
   :alt: GitHub Repo
   :target: https://github.com/lewis-morris/flarchitect



--------------------------------------------



**flarchitect** turns your `SQLAlchemy`_ models into a polished RESTful API complete with interactive `Redoc`_ or Swagger UI documentation.
Hook it into your `Flask`_ application and you'll have endpoints, schemas and docs in moments.

What can it do?

* Automatically detect and create endpoints, including nested relationships.
* Standardise responses with a consistent structure.
* Authenticate users with JWT access and refresh tokens.
* Restrict endpoints to specific roles with :ref:`roles-required`.
* Add configurable rate limits backed by Redis, Memcached or MongoDB.
* Be configured globally in `Flask`_ or per model via ``Meta`` attributes.
* Generate `Redoc`_ or Swagger UI documentation on the fly.
* Extend behaviour with response callbacks, custom validators and per-route hooks (:ref:`advanced-callbacks`).

Advanced Configuration
----------------------

Need finer control? The :doc:`Advanced Configuration <advanced_configuration>` guide covers features like rate limiting, CORS, and custom cache backends.

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

`View Demos <https://github.com/lewis-morris/flarchitect/tree/master/demo>`__

