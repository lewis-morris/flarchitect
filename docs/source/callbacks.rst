Callbacks
=========================================

Callbacks let you hook into the request lifecycle to run custom logic around
database operations and responses. They can be declared globally in the Flask
configuration or on individual SQLAlchemy models.

Lifecycle
---------

flarchitect recognizes four callback types:

* **Setup** – runs before any database operation. Use for validation, logging
  or altering the incoming data.
* **Return** – runs after the operation but before the response is sent.
  Ideal for adjusting the output or adding headers.
* **Error** – runs when an exception bubbles up. Handle logging or
  notifications here.
* **Final** – runs immediately before the response is returned to the client.

Configuration
-------------

Callbacks are referenced by the following configuration keys:

* ``SETUP_CALLBACK``
* ``RETURN_CALLBACK``
* ``ERROR_CALLBACK``

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

``Setup`` and ``return`` callbacks should accept ``**kwargs`` and return the
modified kwargs. Example:

.. code-block:: python

    def my_setup_callback(**kwargs):
        # modify kwargs as needed
        return kwargs

Error callbacks receive the exception and traceback:

.. code-block:: python

    def my_error_callback(exc, tb):
        log_exception(exc, tb)

Post dump callbacks accept ``data`` and ``**kwargs`` and must return the data:

.. code-block:: python

    def my_dump_callback(data, **kwargs):
        data["name"] = data["name"].upper()
        return data

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
