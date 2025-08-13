Getting Started Sample Project
==============================

A minimal application that exposes an ``Author`` model through a generated REST API.
The project lives in ``demo/quickstart/load.py``.

.. literalinclude:: ../../demo/quickstart/load.py
   :language: python
   :linenos:

Run the demo
------------

.. code-block:: bash

   python demo/quickstart/load.py
   curl http://localhost:5000/api/author
