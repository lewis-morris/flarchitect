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
resolver can be supplied via ``API_SESSION_GETTER`` in the Flask config; see
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

    curl http://localhost:5000/api/author

Example response:

.. code:: json

    [
      {"id": 1, "name": "Test Author"}
    ]

A JSON array confirms the API is up and responding as expected.

