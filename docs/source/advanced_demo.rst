Advanced Demo
=============

This annotated example combines soft deletes, nested writes and custom callbacks.
The code lives in ``demo/advanced_features/app.py``.

.. literalinclude:: ../../demo/advanced_features/app.py
   :language: python
   :linenos:

Key points
----------

* **Soft deletes** are enabled via `API_SOFT_DELETE <configuration.html#SOFT_DELETE>`_ and the ``deleted`` column on ``BaseModel`` (see :ref:`soft-delete`).
* **Nested writes** allow creating related objects in one request. ``Book.Meta.allow_nested_writes`` turns it on for books.
* **Custom callbacks** modify behaviour: ``return_callback`` injects a ``debug`` flag into every response and ``Book.Meta.add_callback`` title-cases book names before saving.

Run the demo
------------

.. code-block:: bash

   python demo/advanced_features/app.py
   curl -X POST http://localhost:5000/api/book \
        -H "Content-Type: application/json" \
        -d '{"title": "my book", "author": {"name": "Alice"}}'
   curl http://localhost:5000/api/book?include_deleted=true

For authentication strategies and role management, see :doc:`authentication`
and the :ref:`defining-roles` section.
