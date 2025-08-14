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
   extensions
   openapi
   graphql
   error_handling

.. toctree::
   :maxdepth: 2
   :caption: Configuration
   :hidden:
   
   configuration
   advanced_configuration


.. toctree::
   :maxdepth: 2
   :caption: Advanced Topics
   :hidden:

   advanced_demo

.. toctree::
   :maxdepth: 2
   :caption: Project Info
   :hidden:

   faq
   roadmap

.. image:: /_static/coverage.svg
   :alt: Coverage Report

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

* Automatically create CRUD endpoints for your models, including nested relationships.
* Authenticate users with JWT access and refresh tokens.
* Restrict endpoints to specific roles with :ref:`roles-required`.
* Add configurable rate limits backed by Redis, Memcached or MongoDB.
* Be configured globally in `Flask`_ or per model via ``Meta`` attributes.
* Generate `Redoc`_ or Swagger UI documentation on the fly.
* Extend behaviour with response callbacks, custom validators and per-route hooks (:ref:`advanced-extensions`).

Advanced Configuration
----------------------

Need finer control? The :doc:`Advanced Configuration <advanced_configuration>` guide covers features like rate limiting, CORS, and custom cache backends.

Want to see **flarchitect** in action? Define your models, plug the library into your `Flask`_ app, and you'll get CRUD endpoints, schemas, and interactive docs instantly. The :doc:`Quick Start <quickstart>` walks through a complete example.

`View Demos <https://github.com/lewis-morris/flarchitect/tree/master/demo>`__

