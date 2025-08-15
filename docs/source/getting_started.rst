Getting Started Sample Project
==============================

Flarchitect ships with a tiny demo that shows how it turns a SQLAlchemy model into a REST API.
The sample lives in ``demo/quickstart/load.py`` and defines a single ``Author`` model.
Running the script starts a local server and exposes the model at ``/api/authors``, returning an empty list until you add data.

.. literalinclude:: ../../demo/quickstart/load.py
   :language: python
   :linenos:

Run the demo
------------

.. code-block:: bash

   python demo/quickstart/load.py
   curl http://localhost:5000/api/authors

The curl command answers with a JSON payload that includes some metadata and a ``value`` list of authors.
Because the demo starts with no records, that list is empty:


.. code-block:: json

   {
       "total_count": 0,
       "value": []
   }


Pop open ``http://localhost:5000/docs`` in your browser to explore the automatically generated API docs.
To optionally restrict access, set the `API_DOCUMENTATION_PASSWORD <configuration.html#DOCUMENTATION_PASSWORD>`_ environment variable or enable
`API_DOCUMENTATION_REQUIRE_AUTH <configuration.html#DOCUMENTATION_REQUIRE_AUTH>`_. When protection is active, navigating to ``/docs`` displays a login
screen that accepts either the configured password or valid user credentials.
