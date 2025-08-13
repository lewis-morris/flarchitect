Getting Started Sample Project
==============================

Flarchitect ships with a tiny demo that shows how it turns a SQLAlchemy model into a REST API.
The sample lives in ``demo/quickstart/load.py`` and defines a single ``Author`` model.
Running the script starts a local server and exposes the model at ``/api/author``, returning an empty list until you add data.

.. literalinclude:: ../../demo/quickstart/load.py
   :language: python
   :linenos:

Run the demo
------------

.. code-block:: bash

   python demo/quickstart/load.py
   curl http://localhost:5000/api/author

The curl command answers with a JSON payload that includes some metadata and a ``value`` list of authors.
Because the demo starts with no records, that list is empty:

.. code-block:: json

   {
       "total_count": 0,
       "value": []
   }

Pop open ``http://localhost:5000/docs`` in your browser to explore the automatically generated API docs.
