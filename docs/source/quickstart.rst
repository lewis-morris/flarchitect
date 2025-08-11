Quick Start
=========================================


Installation
-----------------------------------------

Install the package via pip

.. code:: bash

    pip install flarchitect


Model Definition
-----------------------------------------

To enable **flarchitect** to automatically generate API endpoints, it's necessary to provide a valid
`SQLAlchemy`_ session and ensure it can interact with the models designated for API exposure.

This requirement is fulfilled by establishing a base class from which all relevant models will derive.
Additionally, integrating a method named ``get_session`` is essential, as it will facilitate the retrieval of
a SQLAlchemy session.

.. tab-set::

    .. tab-item:: flask-sqlalchemy
        :sync: key1

        **Base Model**

        First you will need a base class that returns a session with a ``get_session`` method.

        When using flask-sqlalchemy, you can return ``db.session`` in your base model.

        .. code:: python

            from sqlalchemy.orm import DeclarativeBase

            class BaseModel(DeclarativeBase):
                def get_session(*args):
                    return db.session

        **Database Models**

        Make sure any model you want to expose has a class attribute called ``Meta`` with the following attributes:

        - ``tag``: The tag that will be used to identify the model in the API and documentation.
        - ``tag_group``: The tag group that the model will be placed in in the API Documentation.

        Don't inherit from your base model, but from ``db.Model`` as you normally would. When using `Flask-SQLAlchemy`_,
        you set the base model when initializing the extension, we will cover that shortly...

        .. code:: python

            class Author(db.Model):
                __table__ = "author"
                class Meta:
                    tag = 'Author'
                    tag_group = "People/Companies"

                ...fields


    .. tab-item:: vanilla sqlalchemy
        :sync: key2

        When using sqlalchemy, you will have to create a session object and return this in your base model.

        .. code:: python

            from sqlalchemy import create_engine
            from sqlalchemy.orm import DeclarativeBase, sessionmaker

            engine = create_engine("sqlite:///example.db", echo=True)
            Session = sessionmaker(bind=engine)
            session = Session()




        .. code:: python

            class BaseModel(DeclarativeBase):
                def get_session(*args):
                    return session

        Make sure any model you want to expose inherits from the correct base, and has a class attribute ``Meta`` with
        the following attributes:

        - ``tag``: The tag that will be used to identify the model in the API and documentation.
        - ``tag_group``: The tag group that the model will be placed in in the API Documentation.


        .. code:: python

            class Author(BaseModel):
                __table__ = "author"
                class Meta:
                    tag = 'Author'
                    tag_group = "People/Companies"

                ...fields

        Due to the default settings in ``flarchitect`` being set to `Flask-SQLAlchemy`_'s ``db.session``, you will
        have to set a `Flask`_ config of ``API_BASE_MODEL`` with the name of your base model.

        i.e

        .. code:: python

            app.config['API_BASE_MODEL'] = 'BaseModel'


Extension Initialization
-----------------------------------------

To initialize the extension, it's necessary to provide **flarchitect** with a valid `Flask`_ application instance
as with many other `Flask`_ extensions.

The only other requirement's are a few configuration values that need to be passed to `Flask`_'s config.

- `API_TITLE <configuration.html#TITLE>`_ - The title of the API that will be displayed in the documentation.
- `API_VERSION <configuration.html#VERSION>`_ - The version of the API that will be displayed in the documentation.
- `API_BASE_MODEL <configuration.html#BASE_MODEL>`_ - This will either be ``db.Model`` if using `Flask-SQLAlchemy`_ or the name of your base model if using vanilla `SQLAlchemy`_.

.. tab-set::

    .. tab-item:: flask-sqlalchemy
        :sync: key1

          Notice below when you initialise `Flask-SQLAlchemy`_ you pass your ``BaseModel`` as the ``model_class`` attribute,
          but pass in ``db.Model`` to the `Flask`_ config as :data:`API_BASE_MODEL`.

        This will mean that ``db.Model`` will inherit from your ``BaseModel`` and all related methods will be available
        to your models.

        .. code:: python

              from flask import Flask
              from flask_sqlalchemy import SQLAlchemy
              from flarchitect.core.architect import Architect

              app = Flask(__name__)

              db = SQLAlchemy(model_class=BaseModel)

              app.config["API_TITLE"] = "My API"
              app.config["API_VERSION"] = "1.0"
              app.config["API_BASE_MODEL"] = db.Model

              architect = Architect(app)

              if __name__ == "__main__":
                  app.run(debug=True)

        .. note:: For comprehensive details on configuration, visit our :doc:`configuration </configuration>` page.

        And that's all folks! Just run the code and you should now have a fully functional API with documentation.

    .. tab-item:: vanilla sqlalchemy
        :sync: key1

        When using `SQLAlchemy`_ you will have to set the `API_BASE_MODEL` in the `Flask`_ config.

        .. code:: python

              from flask import Flask
              from flarchitect.core.architect import Architect

              app = Flask(__name__)

              app.config["API_TITLE"] = "My API"
              app.config["API_VERSION"] = "1.0"
              app.config["API_BASE_MODEL"] = BaseModel

              architect = Architect(app)

              if __name__ == "__main__":
                  app.run(debug=True)

        .. note:: For comprehensive details on configuration, visit our :doc:`configuration </configuration>` page.

        And that's all folks!


API Documentation
-----------------------------------------

You should now have a fully functional API with documentation.

``GET`` /docs


Queries
-----------------------------------------

Writing API calls is simple, and can be done in the following way:

``GET`` /api/author - returns a list of paginated authors.

``GET`` /api/author/1 - returns the author with the id of 1.

``POST`` /api/author - creates a new author.

``PATCH`` /api/author/1 - updates the author with the id of 1.

``DELETE`` /api/author/1 - deletes the author with the id of 1.


More advanced queries can be made by adding query parameters to the URL. This is fully documented in the API
documentation served at ``/docs``.


Full Example
-----------------------------------------

To see a full example of this code, please see the ``demo`` directory in our `repo`_ or view the example - `quickstart demo <https://github.com/arched-dev/flarchitect/blob/master/demo/quickstart/load.py>`_

For more indepth example flask application's start with the `basic factory application <https://github.com/arched-dev/flarchitect/tree/master/demo/basic_factory>`_
For a minimal verified setup, check the unit tests - `test_basic.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_basic.py>`_
