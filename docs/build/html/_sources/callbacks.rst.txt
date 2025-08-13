Callbacks
=========================================

Callbacks let you hook into the request lifecycle to run custom logic around
database operations and responses. They can be declared globally in the Flask
configuration or on individual SQLAlchemy models.

Callback types
--------------

flarchitect recognises a number of callback hooks that allow you to run custom
logic at various stages of processing:

* **Global setup** – runs before any model-specific processing. ``GLOBAL_SETUP_CALLBACK`` (global: ``API_GLOBAL_SETUP_CALLBACK``)
* **Setup** – runs before database operations. Useful for validation, logging
  or altering incoming data. ``SETUP_CALLBACK`` (global: ``API_SETUP_CALLBACK``)
* **Filter** – lets you adjust the SQLAlchemy query object before filtering and
  pagination are applied. ``FILTER_CALLBACK`` (global: ``API_FILTER_CALLBACK``)
* **Add** – called before a new object is committed to the database. ``ADD_CALLBACK`` (global: ``API_ADD_CALLBACK``)
* **Update** – invoked prior to persisting updates to an existing object. ``UPDATE_CALLBACK`` (global: ``API_UPDATE_CALLBACK``)
* **Remove** – executed before an object is deleted. ``REMOVE_CALLBACK`` (global: ``API_REMOVE_CALLBACK``)
* **Return** – runs after the database operation but before the response is
  returned. Ideal for adjusting the output or adding headers. ``RETURN_CALLBACK`` (global: ``API_RETURN_CALLBACK``)
* **Dump** – executes after Marshmallow serialisation allowing you to modify
  the dumped data. ``DUMP_CALLBACK`` (global: ``API_DUMP_CALLBACK``)
* **Final** – runs immediately before the response is sent to the client. ``FINAL_CALLBACK`` (global: ``API_FINAL_CALLBACK``)
* **Error** – triggered when an exception bubbles up; handle logging or
  notifications here. ``ERROR_CALLBACK`` (global: ``API_ERROR_CALLBACK``)

Configuration
-------------

Callbacks are referenced by the following configuration keys (global variants
use ``API_<KEY>``):

* ``GLOBAL_SETUP_CALLBACK`` / ``API_GLOBAL_SETUP_CALLBACK``
* ``SETUP_CALLBACK`` / ``API_SETUP_CALLBACK``
* ``FILTER_CALLBACK`` / ``API_FILTER_CALLBACK``
* ``ADD_CALLBACK`` / ``API_ADD_CALLBACK``
* ``UPDATE_CALLBACK`` / ``API_UPDATE_CALLBACK``
* ``REMOVE_CALLBACK`` / ``API_REMOVE_CALLBACK``
* ``RETURN_CALLBACK`` / ``API_RETURN_CALLBACK``
* ``DUMP_CALLBACK`` / ``API_DUMP_CALLBACK``
* ``FINAL_CALLBACK`` / ``API_FINAL_CALLBACK``
* ``ERROR_CALLBACK`` / ``API_ERROR_CALLBACK``

You can apply these keys in several places:

1. **Global Flask config**

   Use ``API_<KEY>`` to apply a callback to all endpoints.

   .. code-block:: python

      class Config:
          API_SETUP_CALLBACK = my_setup

2. **HTTP method specific config**

   Override the global value for a specific method with ``API_<METHOD>_<KEY>``.

   .. code-block:: python

      class Config:
          API_GET_RETURN_CALLBACK = my_get_return

3. **Model config**

   Set lowercase attributes on a model's ``Meta`` class to apply callbacks to
   all endpoints for that model.

   .. code-block:: python

      class Author(db.Model):
          class Meta:
              setup_callback = my_setup

4. **Model method config**

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

Use ``ADDITIONAL_QUERY_PARAMS`` to document extra query parameters introduced in
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
