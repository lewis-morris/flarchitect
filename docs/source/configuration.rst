Configuration
==============================

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Config Locations:

   config_locations/global_
   config_locations/global_method
   config_locations/model
   config_locations/model_method


Intro
--------------------------------

In ``flarchitect`` configuration values control nearly every aspect of the
generated API and its documentation. Options may be supplied either through
``Flask``'s config object or via ``Meta`` classes on your ``SQLAlchemy``
models.  Global ``Flask`` config keys are prefixed with ``API_`` while model
``Meta`` attributes omit this prefix and use lowercase names.


Config Hierarchy
--------------------------------

To provide flexible overrides **flarchitect** evaluates configuration values in
the following order of precedence:

- **Global** – ``Flask`` config values prefixed with ``API_``.
- **Global Method** – method specific ``Flask`` config values prefixed with
  ``API_{METHOD}_``.
- **Model** – ``Meta`` attributes on a model class.
- **Model Method** – ``Meta`` attributes suffixed with the HTTP method name.

Method or model specific options always override more general configuration.


Documentation Configuration Values
------------------------------------------

These options customise the generated `ReDoc`_ documentation.

.. list-table::

    * - .. data:: CREATE_DOCS
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Create and serve documentation.  Example::

            app.config["API_CREATE_DOCS"] = False

    * - .. data:: DOCUMENTATION_URL
          :bdg:`default:` ``/docs``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - URL used to serve the docs.  Example::

            app.config["API_DOCUMENTATION_URL"] = "/my_docs"

    * - .. data:: TITLE
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-danger:`Required` :bdg-dark-line:`Global`
        - Title displayed in the docs.  Example::

            app.config["API_TITLE"] = "Book Shop API"

    * - .. data:: VERSION
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-danger:`Required` :bdg-dark-line:`Global`
        - Semantic version string. Example::

            app.config["API_VERSION"] = "0.1.0"

    * - .. data:: DESCRIPTION
          :bdg:`default:` ``./flask_schema/html/base_readme.MD``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Markdown description for the docs.  Example::

            app.config["API_DESCRIPTION"] = "README.md"

    * - .. data:: LOGO_URL
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - URL of a logo to display. Example::

            app.config["API_LOGO_URL"] = "https://example.com/logo.png"

    * - .. data:: LOGO_BACKGROUND
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Background colour for the logo. Example::

            app.config["API_LOGO_BACKGROUND"] = "#000000"

    * - .. data:: CONTACT_NAME
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Contact name shown in the docs. Example::

            app.config["API_CONTACT_NAME"] = "Jane Doe"

    * - .. data:: CONTACT_EMAIL
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Contact email address. Example::

            app.config["API_CONTACT_EMAIL"] = "help@example.com"

    * - .. data:: CONTACT_URL
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Contact web page. Example::

            app.config["API_CONTACT_URL"] = "https://example.com/contact"

    * - .. data:: LICENCE_NAME
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Licence name. Example::

            app.config["API_LICENCE_NAME"] = "MIT"

    * - .. data:: LICENCE_URL
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Link to licence text. Example::

            app.config["API_LICENCE_URL"] = "https://opensource.org/licenses/MIT"

    * - .. data:: SERVER_URLS
          :bdg:`default:` ``None``
          :bdg:`type` ``list[dict]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - List of server descriptions. Example::

            app.config["API_SERVER_URLS"] = [{"url": "https://api.example.com"}]

    * - .. data:: DOCUMENTATION_HEADERS
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Custom HTML to inject into ``<head>``. Example::

            app.config["API_DOCUMENTATION_HEADERS"] = "<style>h1{color:red;}</style>"

    * - .. data:: VERBOSITY_LEVEL
          :bdg:`default:` ``0``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Controls console logging verbosity (0–4). Example::

            app.config["API_VERBOSITY_LEVEL"] = 2


API Configuration Values
------------------------------------------

General options for controlling API behaviour.

.. list-table::

    * - .. data:: PREFIX
          :bdg:`default:` ``/api``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Base URL prefix for all endpoints. Example::

            app.config["API_PREFIX"] = "/my_api"

    * - .. data:: READ_ONLY
          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - When ``True`` only ``GET`` requests are permitted. Example::

            app.config["API_READ_ONLY"] = True

    * - .. data:: ALLOWED_METHODS
          :bdg:`default:` ``[]``
          :bdg:`type` ``list[str]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`
        - Restrict models to specific HTTP methods. Example::

            class Meta:
                allowed_methods = ["GET", "POST"]

    * - .. data:: BLOCK_METHODS
          :bdg:`default:` ``[]``
          :bdg:`type` ``list[str]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`
        - Explicit list of methods to block. Example::

            app.config["API_BLOCK_METHODS"] = ["DELETE"]

    * - .. data:: ALLOW_FILTER
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Enable query filtering. Example::

            app.config["API_ALLOW_FILTER"] = False

    * - .. data:: ALLOW_ORDER_BY
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Permit ``order_by`` query parameter. Example::

            class Meta:
                get_allow_order_by = False

    * - .. data:: ALLOW_SELECT_FIELDS
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Allow selecting specific fields via ``fields`` parameter. Example::

            app.config["API_ALLOW_SELECT_FIELDS"] = False

    * - .. data:: FILTER_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Modify query filters before execution. Example::

            app.config["API_FILTER_CALLBACK"] = my_filter

    * - .. data:: ADD_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Called before inserting new records. Example::

            class Meta:
                post_add_callback = my_add_hook

    * - .. data:: UPDATE_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Called before updating records. Example::

            app.config["API_UPDATE_CALLBACK"] = my_update

    * - .. data:: REMOVE_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Called before deleting records. Example::

            class Meta:
                delete_remove_callback = my_remove

    * - .. data:: SERIALIZATION_TYPE
          :bdg:`default:` ``"url"``
          :bdg:`type` ``str | bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`
        - ``"url"`` (links), ``"json"`` (embedded), ``"hybrid```` or ``False``.
          Example::

            app.config["API_SERIALIZATION_TYPE"] = "json"

    * - .. data:: AUTO_VALIDATE
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`
        - Automatically validate incoming payloads. Example::

            class Meta:
                auto_validate = False

    * - .. data:: XML_AS_TEXT
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Return XML responses as ``text/xml`` when enabled.

    * - .. data:: PRINT_EXCEPTIONS
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Print exceptions to console. Example::

            app.config["API_PRINT_EXCEPTIONS"] = False

    * - .. data:: DUMP_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Modify marshalled data before response. Example::

            class Meta:
                get_dump_callback = my_dump

    * - .. data:: FINAL_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global Method`
        - Called just before the response is returned. Example::

            app.config["API_FINAL_CALLBACK"] = finalize

    * - .. data:: DUMP_DATETIME
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Include a ``datetime`` field in responses. Example::

            app.config["API_DUMP_DATETIME"] = False

    * - .. data:: DUMP_VERSION
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Include ``version`` field in responses.

    * - .. data:: DUMP_STATUS_CODE
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Include ``statusCode`` in responses.

    * - .. data:: DUMP_RESPONSE_TIME
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Include response time in ms.

    * - .. data:: DUMP_COUNT
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Include total record count in list responses.

    * - .. data:: DUMP_NULL_NEXT_URL
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Include ``nextUrl`` even when ``None``.

    * - .. data:: DUMP_NULL_PREVIOUS_URL
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Include ``previousUrl`` even when ``None``.

    * - .. data:: DUMP_NULL_ERRORS
          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Include empty ``errors`` field.

    * - .. data:: BASE_MODEL
          :bdg:`default:` ``None``
          :bdg:`type` ``DeclarativeBase``
          :bdg-danger:`Required` :bdg-dark-line:`Global`
        - Base class used for model discovery. Example::

            app.config["API_BASE_MODEL"] = db.Model

    * - .. data:: DUMP_HYBRID_PROPERTIES
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`
        - Include hybrid properties in responses.

    * - .. data:: ADD_RELATIONS
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`
        - Automatically add relationship fields.

    * - .. data:: IGNORE_UNDERSCORE_ATTRIBUTES
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`
        - Hide attributes beginning with ``_``.

    * - .. data:: PAGINATION_SIZE_DEFAULT
          :bdg:`default:` ``20``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Default page size. Example::

            app.config["API_PAGINATION_SIZE_DEFAULT"] = 50

    * - .. data:: PAGINATION_SIZE_MAX
          :bdg:`default:` ``100``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Maximum page size. Example::

            app.config["API_PAGINATION_SIZE_MAX"] = 500

    * - .. data:: RATE_LIMIT
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Apply rate limiting such as ``"5 per minute"``.

    * - .. data:: RATE_LIMIT_STORAGE_URI
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - URI for external rate limit storage backend.

    * - .. data:: ALLOW_NESTED_WRITES
          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Permit POST/PATCH payloads to include related objects.


Authentication Configuration Values
------------------------------------------

.. list-table::

    * - .. data:: AUTHENTICATE
          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`
        - Require authentication for a model or endpoint.

    * - .. data:: AUTHENTICATE_METHOD
          :bdg:`default:` ``None``
          :bdg:`type` ``list[str]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Authentication strategies (``"basic"``, ``"jwt"``, ``"api_key"`` ...).

    * - .. data:: USER_MODEL
          :bdg:`default:` ``None``
          :bdg:`type` ``type``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - SQLAlchemy model used for authentication lookups.

    * - .. data:: USER_LOOKUP_FIELD
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Field on ``USER_MODEL`` used to find users.

    * - .. data:: CREDENTIAL_CHECK_METHOD
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Name of method used to verify credentials.

    * - .. data:: CREDENTIAL_HASH_FIELD
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Field containing a password hash for basic authentication.

    * - .. data:: KEY_AUTH_AND_RETURN_METHOD
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Function returning a user from an API key.

    * - .. data:: CUSTOM_AUTH
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Custom authentication function.


API Callbacks
------------------------------------------

.. list-table::

    * - .. data:: GLOBAL_SETUP_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global Method`
        - Executed before any request. Example::

            app.config["API_GET_GLOBAL_SETUP_CALLBACK"] = setup

    * - .. data:: SETUP_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Per-model pre-processing callback.

    * - .. data:: POST_DUMP_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Modify data after marshmallow dump.

    * - .. data:: DUMP_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Shortcut for method specific post-dump hook.

    * - .. data:: RETURN_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Called before returning the response body.

    * - .. data:: FINAL_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global Method`
        - Executed after :data:`RETURN_CALLBACK` and before the response is sent.

    * - .. data:: ERROR_CALLBACK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global Method`
        - Called when an exception occurs.

    * - .. data:: GLOBAL_PRE_DESERIALIZE_HOOK
          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Hook executed before deserialising incoming payloads.

    * - .. data:: ADDITIONAL_QUERY_PARAMS
          :bdg:`default:` ``None``
          :bdg:`type` ``list[dict]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Extra query parameters to document.


API Method Config (Delete)
------------------------------------------

.. list-table::

    * - .. data:: ALLOW_DELETE_RELATED
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Allow deleting related models via ``delete_related`` query param.

    * - .. data:: ALLOW_DELETE_DEPENDENTS
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`
        - Recursively delete dependent models when ``delete_dependents=1``.

    * - .. data:: ALLOW_CASCADE_DELETE
          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`
        - Permit cascading deletes by passing ``cascade_delete=1``.

    * - .. data:: SOFT_DELETE
          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Mark records as deleted instead of removing them.

    * - .. data:: SOFT_DELETE_ATTRIBUTE
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Attribute storing deletion flag.

    * - .. data:: SOFT_DELETE_VALUES
          :bdg:`default:` ``None``
          :bdg:`type` ``tuple``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Tuple of ``(active, deleted)`` values.


Schema Configuration Values
------------------------------------------

.. list-table::

    * - .. data:: BASE_SCHEMA
          :bdg:`default:` ``AutoSchema``
          :bdg:`type` ``Schema``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Base schema class used for automatic generation.

    * - .. data:: ENDPOINT_CASE
          :bdg:`default:` ``kebab``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Case style for endpoint URLs (``camel``, ``snake``, ``kebab`` ...).

    * - .. data:: FIELD_CASE
          :bdg:`default:` ``snake``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Case style for field names.

    * - .. data:: SCHEMA_CASE
          :bdg:`default:` ``camel``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Case style for schema class names.

