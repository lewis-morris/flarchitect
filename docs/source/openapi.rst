OpenAPI Specification
=========================================

flarchitect automatically generates an OpenAPI 3.0.2 document for every
registered model. The specification powers the interactive Redoc page and
can also be reused with external tools like Postman or Swagger UI.

Automatic generation
--------------------

When ``API_CREATE_DOCS`` is enabled (it is ``True`` by default) the
specification is built on start-up by inspecting the routes and schemas
registered with :class:`flarchitect.Architect`.  Any models
added later are included the next time the application boots.

Accessing the spec
------------------

The generated schema is served at ``/openapi.json``.  You can expose it
manually if you prefer:

.. code-block:: python

    from flask import Flask, Response, jsonify
    from flarchitect import Architect

    app = Flask(__name__)
    architect = Architect(app)

    @app.get("/openapi.json")
    def openapi() -> Response:
        return jsonify(architect.api_spec.to_dict())

Exporting to a file
-------------------

To generate a static JSON document for deployment or tooling:

.. code-block:: python

    import json

    with open("openapi.json", "w") as fh:
        json.dump(architect.api_spec.to_dict(), fh, indent=2)

Customising the document
------------------------

A number of configuration keys let you tailor the output:

* ``API_TITLE`` – title displayed in the document
* ``API_VERSION`` – semantic version string
* ``API_DESCRIPTION`` – path to a README-style file rendered into the
  ``info`` section
* ``API_LOGO_URL`` and ``API_LOGO_BACKGROUND`` – brand the Redoc page

See :doc:`configuration` for the full list of options.

