API Documentation
=========================================

flarchitect automatically generates an OpenAPI 3.0.2 document for every
registered model. The specification powers an interactive documentation page
which can be served with either Redoc or Swagger UI. The raw specification is
standard OpenAPI and can be consumed by external tools such as Postman.

Documentation style
-------------------

By default, flarchitect renders docs with Redoc. To switch to Swagger UI set
`API_DOCS_STYLE <configuration.html#DOCS_STYLE>`_ = "swagger" in your Flask configuration. The only accepted
values are ``"redoc"`` and ``"swagger"``. Redoc provides a clean read-only
reference, while Swagger UI adds an interactive "try it out" console:

.. code-block:: python

    app.config["API_DOCS_STYLE"] = "swagger"

The documentation itself is hosted at `API_DOCUMENTATION_URL <configuration.html#DOCUMENTATION_URL>`_ (default
``/docs``).

Automatic generation
--------------------

When `API_CREATE_DOCS <configuration.html#CREATE_DOCS>`_ is enabled (it is ``True`` by default) the
specification is built on start-up by inspecting the routes and schemas
registered with :class:`flarchitect.Architect`.  Any models
added later are included the next time the application boots.

Accessing the spec
------------------

The canonical JSON schema is served under the docs path at ``/docs/apispec.json``
and is configurable via ``API_DOCS_SPEC_ROUTE``. The legacy top‑level path
``/openapi.json`` (``API_SPEC_ROUTE``) now redirects to the docs JSON and will be
removed in a future release.

Security scheme
---------------

flarchitect defines a ``bearerAuth`` security scheme using HTTP bearer tokens
with JWTs. Routes that require authentication reference this scheme via a
``security`` declaration instead of documenting an explicit ``Authorization``
header parameter.

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

* `API_DOCUMENTATION_HEADERS <configuration.html#DOCUMENTATION_HEADERS>`_ – HTML string inserted into the ``<head>`` of
  the docs page. Use for meta tags or custom scripts.
* `API_TITLE <configuration.html#TITLE>`_ – plain text displayed as the documentation title.
* `API_VERSION <configuration.html#VERSION>`_ – semantic version string such as ``"1.0.0"``.
* `API_DESCRIPTION <configuration.html#DESCRIPTION>`_ – free text or a filepath to a README-style file rendered
  into the ``info`` section.
* `API_LOGO_URL <configuration.html#LOGO_URL>`_ – URL or static path to an image used as the logo.
* `API_LOGO_BACKGROUND <configuration.html#LOGO_BACKGROUND>`_ – CSS colour value behind the logo (e.g.
  ``"#fff"`` or ``"transparent"``).
* `API_CONTACT_NAME <configuration.html#CONTACT_NAME>`_, `API_CONTACT_EMAIL <configuration.html#CONTACT_EMAIL>`_,
  `API_CONTACT_URL <configuration.html#CONTACT_URL>`_ – contact information shown in the spec.
* `API_LICENCE_NAME <configuration.html#LICENCE_NAME>`_, `API_LICENCE_URL <configuration.html#LICENCE_URL>`_ – licence metadata.
* `API_SERVER_URLS <configuration.html#SERVER_URLS>`_ – list of server entries (``url`` + ``description``) for environments.

For example, to load a Markdown file into the specification's info section:

.. code-block:: python

    app.config["API_DESCRIPTION"] = "docs/README.md"

The contents of ``docs/README.md`` are rendered in the spec's ``info`` section.

See :doc:`configuration` for the full list of options.

Error responses in the spec
---------------------------

flarchitect includes common error responses in each operation based on your
configuration and the route’s context:

- 401/403: shown when ``API_AUTHENTICATE`` is enabled, or when a route explicitly declares them (e.g., ``/auth/refresh``).
- 429: shown when a rate limit is configured via ``API_RATE_LIMIT``; standard rate-limit headers are documented.
- 400: shown when a request body is validated (input schema present) or for list endpoints with filtering/pagination features enabled.
- 422: shown on ``POST``/``PUT``/``PATCH`` for models, reflecting integrity/type errors.
- 404: shown for single-resource lookups and relationship endpoints.
- 409: shown for ``DELETE`` (conflicts with related data or cascade rules).
- 500: included by default unless you override the error list.

You can override the default set for a specific route by supplying
``error_responses=[...]`` to ``@architect.schema_constructor``.
