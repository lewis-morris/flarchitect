Extensions
=========================================

Callbacks let you hook into the request lifecycle to run custom logic around
database operations and responses. They can be declared globally in the Flask
configuration or on individual SQLAlchemy models.

.. note::

   With ``AUTO_NAME_ENDPOINTS`` enabled (the default), flarchitect generates a
   summary for each endpoint based on its schema and HTTP method. Disable this
   flag if your callbacks provide custom summaries to prevent them from being
   overwritten.

Callback types
--------------

flarchitect recognises a number of callback hooks that allow you to run custom
logic at various stages of processing:

* **Global setup** – runs before any model-specific processing. ``GLOBAL_SETUP_CALLBACK`` (global: `API_GLOBAL_SETUP_CALLBACK <configuration.html#GLOBAL_SETUP_CALLBACK>`_)
* **Setup** – runs before database operations. Useful for validation, logging
  or altering incoming data. ``SETUP_CALLBACK`` (global: `API_SETUP_CALLBACK <configuration.html#SETUP_CALLBACK>`_)
* **Filter** – lets you adjust the SQLAlchemy query object before filtering and
  pagination are applied. ``FILTER_CALLBACK`` (global: `API_FILTER_CALLBACK <configuration.html#FILTER_CALLBACK>`_)
* **Add** – called before a new object is committed to the database. ``ADD_CALLBACK`` (global: `API_ADD_CALLBACK <configuration.html#ADD_CALLBACK>`_)
* **Update** – invoked prior to persisting updates to an existing object. ``UPDATE_CALLBACK`` (global: `API_UPDATE_CALLBACK <configuration.html#UPDATE_CALLBACK>`_)
* **Remove** – executed before an object is deleted. ``REMOVE_CALLBACK`` (global: `API_REMOVE_CALLBACK <configuration.html#REMOVE_CALLBACK>`_)
* **Return** – runs after the database operation but before the response is
  returned. Ideal for adjusting the output or adding headers. ``RETURN_CALLBACK`` (global: `API_RETURN_CALLBACK <configuration.html#RETURN_CALLBACK>`_)
* **Dump** – executes after Marshmallow serialisation allowing you to modify
  the dumped data. ``DUMP_CALLBACK`` (global: `API_DUMP_CALLBACK <configuration.html#DUMP_CALLBACK>`_)
* **Final** – runs immediately before the response is sent to the client. ``FINAL_CALLBACK`` (global: `API_FINAL_CALLBACK <configuration.html#FINAL_CALLBACK>`_)
* **Error** – triggered when an exception bubbles up; handle logging or
  notifications here. ``ERROR_CALLBACK`` (global: `API_ERROR_CALLBACK <configuration.html#ERROR_CALLBACK>`_)

Configuration
-------------

Callbacks are referenced by the following configuration keys (global variants
use ``API_<KEY>``):

* ``GLOBAL_SETUP_CALLBACK`` / `API_GLOBAL_SETUP_CALLBACK <configuration.html#GLOBAL_SETUP_CALLBACK>`_
* ``SETUP_CALLBACK`` / `API_SETUP_CALLBACK <configuration.html#SETUP_CALLBACK>`_
* ``FILTER_CALLBACK`` / `API_FILTER_CALLBACK <configuration.html#FILTER_CALLBACK>`_
* ``ADD_CALLBACK`` / `API_ADD_CALLBACK <configuration.html#ADD_CALLBACK>`_
* ``UPDATE_CALLBACK`` / `API_UPDATE_CALLBACK <configuration.html#UPDATE_CALLBACK>`_
* ``REMOVE_CALLBACK`` / `API_REMOVE_CALLBACK <configuration.html#REMOVE_CALLBACK>`_
* ``RETURN_CALLBACK`` / `API_RETURN_CALLBACK <configuration.html#RETURN_CALLBACK>`_
* ``DUMP_CALLBACK`` / `API_DUMP_CALLBACK <configuration.html#DUMP_CALLBACK>`_
* ``FINAL_CALLBACK`` / `API_FINAL_CALLBACK <configuration.html#FINAL_CALLBACK>`_
* ``ERROR_CALLBACK`` / `API_ERROR_CALLBACK <configuration.html#ERROR_CALLBACK>`_

You can apply these keys in several places:

1. **Global Flask config**

   Use ``API_<KEY>`` to apply a callback to all endpoints.

   .. code-block:: python

      class Config:
          API_SETUP_CALLBACK = my_setup

2. **Model config**

   Set lowercase attributes on a model's ``Meta`` class to apply callbacks to
   all endpoints for that model.

   .. code-block:: python

      class Author(db.Model):
          class Meta:
              setup_callback = my_setup

3. **Model method config**

   Use ``<method>_<key>`` on the ``Meta`` class for the highest level of
   specificity.

   .. code-block:: python

      class Author(db.Model):
          class Meta:
              get_return_callback = my_get_return

Callback signatures
-------------------

Setup, Global setup and filter
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Setup-style callbacks should accept ``model`` and ``**kwargs`` and return the
modified kwargs:

.. code-block:: python

    def my_setup_callback(model, **kwargs):
        # modify kwargs as needed
        return kwargs

    def my_filter_callback(query, model, params):
        return query.filter(model.id > 0)

Add, update and remove
^^^^^^^^^^^^^^^^^^^^^^

These callbacks receive the SQLAlchemy object instance and must return it:

.. code-block:: python

    def my_add_callback(obj, model):
        obj.created_by = "system"
        return obj

Return
^^^^^^

Return callbacks receive ``model`` and ``output`` and must return a dictionary
containing the ``output`` key:

.. code-block:: python

    def my_return_callback(model, output, **kwargs):
        return {"output": output}

Dump
^^^^

Dump callbacks accept ``data`` and ``**kwargs`` and must return the data:

.. code-block:: python

    def my_dump_callback(data, **kwargs):
        data["name"] = data["name"].upper()
        return data

Final
^^^^^

Final callbacks receive the response dictionary before it is serialised:

.. code-block:: python

    def my_final_callback(data):
        data["processed"] = True
        return data

Error
^^^^^

Error callbacks receive the error message, status code and original value:

.. code-block:: python

    def my_error_callback(error, status_code, value):
        log_exception(error)

Extending query parameters
--------------------------

Use `ADDITIONAL_QUERY_PARAMS <configuration.html#ADDITIONAL_QUERY_PARAMS>`_ to document extra query parameters introduced in
a return callback. The value is a list of OpenAPI parameter objects.

.. code-block:: python

    class Config:
        API_ADDITIONAL_QUERY_PARAMS = [{
            "name": "log",
            "in": "query",
            "description": "Log call into the database",
            "schema": {"type": "string"},
        }]

    class Author(db.Model):
        class Meta:
            get_additional_query_params = [{
                "name": "log",
                "in": "query",
                "schema": {"type": "string"},
            }]

Acceptable types
----------------

``schema.type`` may be one of:

* ``string``
* ``number``
* ``integer``
* ``boolean``
* ``array``
* ``object``

Acceptable formats
------------------

Common ``schema.format`` values include:

* ``date``
* ``date-time``
* ``password``
* ``byte``
* ``binary``
* ``email``
* ``phone``
* ``postal_code``
* ``uuid``
* ``uri``
* ``hostname``
* ``ipv4``
* ``ipv6``
* ``int32``
* ``int64``
* ``float``
* ``double``

For comprehensive configuration details see :doc:`configuration`.
