API Documentation
=========================================

flarchitect automatically generates an OpenAPI 3.0.2 document for every
registered model. The specification powers an interactive documentation page
which can be served with either Redoc or Swagger UI. The raw specification is
standard OpenAPI and can be consumed by external tools such as Postman.

Documentation style
-------------------

By default, flarchitect renders docs with Redoc. To switch to Swagger UI set
``API_DOCS_STYLE = "swagger"`` in your Flask configuration. The only accepted
values are ``"redoc"`` and ``"swagger"``. Redoc provides a clean read-only
reference, while Swagger UI adds an interactive "try it out" console:

.. code-block:: python

    app.config["API_DOCS_STYLE"] = "swagger"

The documentation itself is hosted at ``API_DOCUMENTATION_URL`` (default
``/docs``).

Automatic generation
--------------------

When ``API_CREATE_DOCS`` is enabled (it is ``True`` by default) the
specification is built on start-up by inspecting the routes and schemas
registered with :class:`flarchitect.Architect`.  Any models
added later are included the next time the application boots.

Accessing the spec
------------------

The generated schema is automatically served at ``/openapi.json``. Override
the URL with ``API_SPEC_ROUTE`` if you need to mount the document elsewhere.

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

* ``API_DOCUMENTATION_HEADERS`` – HTML string inserted into the ``<head>`` of
  the docs page. Use for meta tags or custom scripts.
* ``API_TITLE`` – plain text displayed as the documentation title.
* ``API_VERSION`` – semantic version string such as ``"1.0.0"``.
* ``API_DESCRIPTION`` – free text or a filepath to a README-style file rendered
  into the ``info`` section.
* ``API_LOGO_URL`` – URL or static path to an image used as the logo.
* ``API_LOGO_BACKGROUND`` – CSS colour value behind the logo (e.g.
  ``"#fff"`` or ``"transparent"``).

See :doc:`configuration` for the full list of options.

