Quick Start
========================================

This guide walks you through building a minimal API with **flarchitect**. You'll define your models,
configure a Flask application, spin up the server, and test the endpoints.

Installation
----------------------------------------

Install the package via pip.

.. code:: bash

    pip install flarchitect

Define your models
----------------------------------------

Define your models using SQLAlchemy. ``flarchitect`` automatically resolves
the active database session, whether you're using Flask-SQLAlchemy or plain
SQLAlchemy, so no special ``get_session`` method is required.

.. code:: python

    from flask_sqlalchemy import SQLAlchemy
    from sqlalchemy.orm import DeclarativeBase

    class BaseModel(DeclarativeBase):
        pass

    db = SQLAlchemy(model_class=BaseModel)

    class Author(db.Model):
        __tablename__ = "author"

        class Meta:
            tag = "Author"
            tag_group = "People/Companies"

This setup gives **flarchitect** access to your models. The library automatically
locates the active SQLAlchemy session. For non-Flask setups, a custom session
resolver can be supplied via `API_SESSION_GETTER <configuration.html#SESSION_GETTER>`_ in the Flask config; see
:ref:`custom-session-getter` for details.

Configure Flask
----------------------------------------

Register the extension with a Flask app and supply configuration values.

.. code:: python

    from flask import Flask
    from flarchitect import Architect

    app = Flask(__name__)

    app.config["API_TITLE"] = "My API"
    app.config["API_VERSION"] = "1.0"
    app.config["API_BASE_MODEL"] = db.Model

    architect = Architect(app)

These settings tell **flarchitect** how to build the API and where to find your models.

Spin up the app
----------------------------------------

Run the development server to expose the generated routes.

.. code:: python

    if __name__ == "__main__":
        app.run(debug=True)

Launching the server makes the automatically generated API available.

Test the endpoints
----------------------------------------

Use ``curl`` to call an endpoint and view the response.

.. code:: bash

    curl http://localhost:5000/api/authors

Example response:

.. code:: json

    {
      "datetime": "2024-01-01T00:00:00.0000+00:00",
      "api_version": "0.1.0",
      "status_code": 200,
      "response_ms": 15,
      "total_count": 1,
      "next_url": null,
      "previous_url": null,
      "errors": null,
      "value": [
        {"id": 1, "name": "Test Author"}
      ]
    }

This structured payload is produced by :func:`create_response` and shows the
standard metadata flarchitect includes by default. To return a bare list,
disable the metadata fields via the ``API_DUMP_*`` configuration options, for example:

- `API_DUMP_DATETIME <configuration.html#DUMP_DATETIME>`_
- `API_DUMP_VERSION <configuration.html#DUMP_VERSION>`_
- `API_DUMP_STATUS_CODE <configuration.html#DUMP_STATUS_CODE>`_
- `API_DUMP_RESPONSE_MS <configuration.html#DUMP_RESPONSE_MS>`_
- `API_DUMP_TOTAL_COUNT <configuration.html#DUMP_TOTAL_COUNT>`_

From Model to API
----------------------------------------

Turn this:

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

Next steps
----------------------------------------

To secure the API and define user roles, see :doc:`authentication` and the
:ref:`defining-roles` section.
