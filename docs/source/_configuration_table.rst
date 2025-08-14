Core Settings
-------------

Essential configuration values needed to run ``flarchitect`` and control automatic route generation.

.. list-table::

    * - ``API_TITLE``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - Sets the display title of the generated documentation. Provide a concise project name or API identifier. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_VERSION``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - Defines the version string shown in the docs header, helping consumers track API revisions. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``FULL_AUTO``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When ``True`` ``flarchitect`` registers CRUD routes for all models at
          startup. Set to ``False`` to define routes manually.

        Example::

              class Config:
                  FULL_AUTO = False

    * - ``AUTO_NAME_ENDPOINTS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Automatically generates OpenAPI summaries from the schema and HTTP
          method when no summary is supplied. Disable to preserve custom
          summaries.

          Example::

              class Config:
                  AUTO_NAME_ENDPOINTS = False


Optional Settings
-----------------

Documentation Settings
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::

    * - ``API_CREATE_DOCS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Controls whether ReDoc documentation is generated automatically. Set to ``False`` to disable docs in production or when using an external documentation tool. Accepts ``True`` or ``False``. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DOCUMENTATION_HEADERS``

          :bdg:`default:` ````
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Extra HTML placed in the <head> of the docs page. Supply meta tags or script includes as a string or template.
    * - ``API_DOCUMENTATION_URL``

          :bdg:`default:` ``/docs``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - URL path where documentation is served. Useful for mounting docs under a custom route such as ``/redoc``. Accepts any valid path string. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DOCUMENTATION_PASSWORD``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Protects docs and ``apispec.json`` with a simple password prompt. Users must enter this password on the docs login screen.
    * - ``API_DOCUMENTATION_REQUIRE_AUTH``

          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When ``True`` the docs login screen accepts user account credentials in addition to the optional password. Requires ``API_AUTHENTICATE_METHOD`` to be configured.
    * - ``API_DOCS_STYLE``

          :bdg:`default:` ``redoc``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Selects the documentation UI style. Use ``redoc`` (default) or ``swagger`` to render with Swagger UI.
    * - ``API_SPEC_ROUTE``

          :bdg:`default:` ``/openapi.json``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Path where the raw OpenAPI document is served. Override to change the
          URL exposed by the automatic endpoint.
    * - ``API_LOGO_URL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - URL or path to an image used as the documentation logo. Useful for branding or product recognition. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_LOGO_BACKGROUND``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Sets the background colour behind the logo, allowing alignment with corporate branding. Accepts any CSS colour string. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DESCRIPTION``

          :bdg:`type` ``str or str path``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Accepts free text or a filepath to a Jinja template and supplies the description shown on the docs landing page. Useful for providing an overview or dynamically generated content using ``{config.xxxx}`` placeholders. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_CONTACT_NAME``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Human-readable name for API support or maintainer shown in the docs. Leave ``None`` to omit the contact block. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_CONTACT_EMAIL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Email address displayed for support requests. Use when consumers need a direct channel for help. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_CONTACT_URL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Website or documentation page for further assistance. Set to ``None`` to hide the link. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_LICENCE_NAME``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Name of the licence governing the API, e.g., ``MIT`` or ``Apache-2.0``. Helps consumers understand usage rights. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_LICENCE_URL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - URL linking to the full licence text for transparency. Set to ``None`` to omit. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SERVER_URLS``

          :bdg:`default:` ``None``
          :bdg:`type` ``list[dict]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - List of server objects defining environments where the API is hosted. Each dict may include ``url`` and ``description`` keys. Ideal for multi-environment setups. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DOC_HTML_HEADERS``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - HTML ``<head>`` snippets inserted into the documentation page. Use to add meta tags or analytics scripts. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.

Routing and Behaviour
~~~~~~~~~~~~~~~~~~~~~

.. list-table::

    * - ``API_PREFIX``

          :bdg:`default:` ``/api``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Base path prefix applied to all API routes. Adjust when mounting the API under a subpath such as ``/v1``. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_CACHE_TYPE``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Flask-Caching backend used for caching ``GET`` responses. Specify
          names like ``RedisCache`` when the ``flask-caching`` package is
          installed. Without that dependency, only ``SimpleCache`` is supported
          through a small built-in fallback; other values raise a runtime
          error.

    * - ``API_CACHE_TIMEOUT``

          :bdg:`default:` ``300``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Expiry time in seconds for cached responses. Only applicable when ``API_CACHE_TYPE`` is set. See :ref:`api_caching`.
    * - ``API_ENABLE_CORS``

          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Enables Cross-Origin Resource Sharing. If ``flask-cors`` is present
          the settings are delegated to it; otherwise a minimal
          ``Access-Control-Allow-Origin`` header is applied based on
          ``CORS_RESOURCES``.
    * - ``API_XML_AS_TEXT``

          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When ``True``, XML responses are served with ``text/xml`` instead of ``application/xml`` for broader client compatibility.
    * - ``API_VERBOSITY_LEVEL``

          :bdg:`default:` ``1``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Verbosity for console output during API generation. ``0`` silences logs while higher values provide more detail. Example: `tests/test_model_meta/model_meta/config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_model_meta/model_meta/config.py>`_.
    * - ``API_ENDPOINT_CASE``

          :bdg:`default:` ``kebab``
          :bdg:`type` ``string``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Case style for generated endpoint URLs such as ``kebab`` or ``snake``. Choose to match your project's conventions. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ENDPOINT_NAMER``

          :bdg:`default:` ``endpoint_namer``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Function that generates endpoint names from models. Override to customise URL naming behaviour.

Serialization Settings
~~~~~~~~~~~~~~~~~~~~~~

.. list-table::

    * - ``API_FIELD_CASE``

          :bdg:`default:` ``snake``
          :bdg:`type` ``string``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Determines the case used for field names in responses, e.g., ``snake`` or ``camel``. Helps integrate with client expectations. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SCHEMA_CASE``

          :bdg:`default:` ``camel``
          :bdg:`type` ``string``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Naming convention for generated schemas. Options include ``camel`` or ``snake`` depending on tooling preferences. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_PRINT_EXCEPTIONS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Toggles Flask's exception printing in responses. Disable in production for cleaner error messages. Options: ``True`` or ``False``.
    * - ``API_BASE_MODEL``

          :bdg:`default:` ``None``
          :bdg:`type` ``Model``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Root SQLAlchemy model used for generating documentation and inferring defaults. Typically the base ``db.Model`` class.
    * - ``API_BASE_SCHEMA``

          :bdg:`default:` ``AutoSchema``
          :bdg:`type` ``Schema``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Base schema class used for model serialization. Override with a custom schema to adjust marshmallow behaviour. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_AUTO_VALIDATE``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Automatically validate incoming data against field types and formats. Disable for maximum performance at the risk of accepting invalid data.
    * - ``API_GLOBAL_PRE_DESERIALIZE_HOOK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Callable run on the raw request body before deserialization. Use it to normalise or sanitize payloads globally.
    * - ``API_ALLOW_CASCADE_DELETE``

          :bdg-secondary:`Optional` 

        - Allows cascading deletes on related models when a parent is removed. Use with caution to avoid accidental data loss. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_IGNORE_UNDERSCORE_ATTRIBUTES``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Ignores attributes prefixed with ``_`` during serialization to keep internal fields hidden. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SERIALIZATION_TYPE``

          :bdg-secondary:`Optional`

        - Output format for serialized data. Options include ``url`` (default), ``json``, ``dynamic`` and ``hybrid``. Determines how responses are rendered. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SERIALIZATION_DEPTH``

          :bdg-secondary:`Optional` 

        - Depth for nested relationship serialization. Higher numbers include deeper related objects, impacting performance.
    * - ``API_DUMP_HYBRID_PROPERTIES``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Includes hybrid SQLAlchemy properties in serialized output. Disable to omit computed attributes. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ADD_RELATIONS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Adds relationship fields to serialized output, enabling nested data representation. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_PAGINATION_SIZE_DEFAULT``

          :bdg:`default:` ``20``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Default number of items returned per page when pagination is enabled. Set lower for lightweight responses. Example: `tests/test_api_filters.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_api_filters.py>`_.
    * - ``API_PAGINATION_SIZE_MAX``

          :bdg:`default:` ``100``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Maximum allowed page size to prevent clients requesting excessive data. Adjust based on performance considerations.
    * - ``API_READ_ONLY``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - When ``True``, only read operations are allowed on models, blocking writes for safety. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.

Query Options
~~~~~~~~~~~~~

.. list-table::

    * - ``API_ALLOW_ORDER_BY``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Enables ``order_by`` query parameter to sort results. Disable to enforce fixed ordering. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ALLOW_FILTERS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Allows filtering using query parameters. Useful for building rich search functionality. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ALLOW_JOIN``

          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Enables ``join`` query parameter to include related resources in queries.
    * - ``API_ALLOW_GROUPBY``

          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Enables ``groupby`` query parameter for grouping results.
    * - ``API_ALLOW_AGGREGATION``

          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Allows aggregate functions like ``field|label__sum`` for summarising data.
    * - ``API_ALLOW_SELECT_FIELDS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Allows clients to specify which fields to return, reducing payload size. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.

Method Access Control
~~~~~~~~~~~~~~~~~~~~~

.. list-table::

    * - ``API_ALLOWED_METHODS``

          :bdg:`default:` ``[]``
          :bdg:`type` ``list[str]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Explicit list of HTTP methods permitted on routes. Only methods in this list are enabled.
    * - ``API_BLOCK_METHODS``

          :bdg:`default:` ``[]``
          :bdg:`type` ``list[str]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Methods that should be disabled even if allowed elsewhere, e.g., ``["DELETE", "POST"]`` for read-only APIs.

Authentication Settings
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::

    * - ``API_AUTHENTICATE``

          :bdg-secondary:`Optional` 

        - Enables authentication on all routes. When provided, requests must pass the configured authentication check. Example: `tests/test_authentication.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_authentication.py>`_.
    * - ``API_AUTHENTICATE_METHOD``

          :bdg-secondary:`Optional` 

        - Name of the authentication method used, such as ``jwt`` or ``basic``. Determines which auth backend to apply. Example: `tests/test_authentication.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_authentication.py>`_.
    * - ``API_CREDENTIAL_HASH_FIELD``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Field on the user model storing a hashed credential for API key auth. Required when using ``api_key`` authentication.
    * - ``API_CREDENTIAL_CHECK_METHOD``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Name of the method on the user model that validates a plaintext credential, such as ``check_password``.
    * - ``API_KEY_AUTH_AND_RETURN_METHOD``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Custom function for API key auth that receives a key and returns the matching user object.
    * - ``API_USER_LOOKUP_FIELD``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Attribute used to locate a user, e.g., ``username`` or ``email``.
    * - ``API_CUSTOM_AUTH``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Callable invoked when ``API_AUTHENTICATE_METHOD`` includes ``"custom"``. It must return the authenticated user or ``None``.
    * - ``API_USER_MODEL``

            :bdg-secondary:`Optional`

          - Import path for the user model leveraged during authentication workflows. Example: `tests/test_authentication.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_authentication.py>`_.
    * - ``API_JWT_EXPIRY_TIME``

          :bdg:`default:` ``360``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Minutes an access token remains valid before requiring a refresh.
    * - ``API_JWT_REFRESH_EXPIRY_TIME``

          :bdg:`default:` ``2880``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Minutes a refresh token stays valid. Defaults to two days (``2880`` minutes).

Callback Hooks
~~~~~~~~~~~~~~

.. list-table::

    * - ``API_GLOBAL_SETUP_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Runs before any model-specific processing.
    * - ``API_FILTER_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Adjusts the SQLAlchemy query before filters or pagination are applied.
    * - ``API_ADD_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Invoked prior to committing a new object to the database.
    * - ``API_UPDATE_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Called before persisting changes to an existing object.
    * - ``API_REMOVE_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Executed before deleting an object from the database.
    * - ``API_SETUP_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Function executed before processing a request, ideal for setup tasks or validation. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_RETURN_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Callback invoked to modify the response payload before returning it to the client. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ERROR_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Error-handling hook allowing custom formatting or logging of exceptions. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Post-serialization hook to adjust data after Marshmallow dumping.
    * - ``API_FINAL_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Executes just before the response is serialized and returned to the client.
    * - ``API_ADDITIONAL_QUERY_PARAMS``

          :bdg:`default:` ``None``
          :bdg:`type` ``list[dict]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Extra query parameters supported by the endpoint. Each dict may contain ``name`` and ``schema`` keys. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.

Response Metadata
~~~~~~~~~~~~~~~~~

.. list-table::

    * - ``API_DUMP_DATETIME``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Appends the current UTC timestamp to responses for auditing. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_VERSION``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Includes the API version string in every payload. Helpful for client-side caching. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_STATUS_CODE``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Adds the HTTP status code to the serialized output, clarifying request outcomes. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_RESPONSE_MS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Adds the elapsed request processing time in milliseconds to each response.
    * - ``API_DUMP_TOTAL_COUNT``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Includes the total number of available records in list responses, aiding pagination UX.
    * - ``API_DUMP_NULL_NEXT_URL``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When pagination reaches the end, returns ``null`` for ``next`` URLs instead of omitting the key. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_NULL_PREVIOUS_URL``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Ensures ``previous`` URLs are present even when no prior page exists by returning ``null``. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_NULL_ERRORS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Ensures an ``errors`` key is always present in responses, defaulting to ``null`` when no errors occurred. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.

Rate Limiting and Sessions
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::

    * - ``API_RATE_LIMIT``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Rate limit string using Flask-Limiter syntax (e.g., ``100/minute``) to throttle requests. Example: `tests/test_flask_config.py <https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_RATE_LIMIT_STORAGE_URI``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - URI for the rate limiter's storage backend, e.g., ``redis://127.0.0.1:6379``.
          When omitted, ``flarchitect`` probes for Redis, Memcached, or MongoDB and falls back to in-memory storage.
          Use this to pin rate limiting to a specific service instead of auto-detection.
    * - ``API_SESSION_GETTER``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Callable returning a SQLAlchemy :class:`~sqlalchemy.orm.Session`.
          Provides manual control over session retrieval when automatic
          resolution is insufficient, such as with custom session factories
          or multiple database binds. If unset, ``flarchitect`` attempts to
          locate the session via Flask-SQLAlchemy, model ``query`` attributes,
          or engine bindings.

Field Inclusion Controls
~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::

    * - ``IGNORE_FIELDS``

          :bdg:`default:` ``None``
          :bdg:`type` ``list[str]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Intended list of attributes hidden from both requests and responses.
          Use it when a column should never be accepted or exposed, such as ``internal_notes``.
          At present the core does not process this flag, so filtering must be handled manually.
    * - ``IGNORE_OUTPUT_FIELDS``

          :bdg:`default:` ``None``
          :bdg:`type` ``list[str]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Fields accepted during writes but stripped from serialized responses—ideal for secrets like ``password``.
          This option is not yet wired into the serializer; custom schema logic is required to enforce it.
    * - ``IGNORE_INPUT_FIELDS``

          :bdg:`default:` ``None``
          :bdg:`type` ``list[str]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Attributes the API ignores if clients supply them, while still returning the values when present on the model.
          Useful for server-managed columns such as ``created_at``.
          Currently this flag is informational and does not trigger automatic filtering.

Soft Delete
~~~~~~~~~~~

.. list-table::

    * - ``API_SOFT_DELETE``

          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Marks records as deleted rather than removing them from the database. See :ref:`soft-delete`.
          When enabled, ``DELETE`` swaps a configured attribute to its "deleted" value unless ``?cascade_delete=1`` is sent.
        - Example::

              class Config:
                  API_SOFT_DELETE = True
    * - ``API_SOFT_DELETE_ATTRIBUTE``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Model column that stores the delete state, such as ``status`` or ``is_deleted``.
          ``flarchitect`` updates this attribute to the "deleted" value during soft deletes.
          Example::

              API_SOFT_DELETE_ATTRIBUTE = "status"
    * - ``API_SOFT_DELETE_VALUES``

          :bdg:`default:` ``None``
          :bdg:`type` ``tuple``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Two-element tuple defining the active and deleted markers for ``API_SOFT_DELETE_ATTRIBUTE``.
          For example, ``("active", "deleted")`` or ``(1, 0)``.
          The second value is written when a soft delete occurs.
    * - ``API_ALLOW_DELETE_RELATED``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Historical flag intended to control whether child records are deleted alongside their parent.
          The current deletion engine only honours ``API_ALLOW_CASCADE_DELETE``, so this setting is ignored.
          Leave it unset unless future versions reintroduce granular control.
    * - ``API_ALLOW_DELETE_DEPENDENTS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Companion flag to ``API_ALLOW_DELETE_RELATED`` covering association-table entries and similar dependents.
          Not currently evaluated by the code base; cascade behaviour hinges solely on ``API_ALLOW_CASCADE_DELETE``.
          Documented for completeness and potential future use.

Endpoint Summaries
~~~~~~~~~~~~~~~~~~

.. list-table::

    * - ``GET_MANY_SUMMARY``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Customises the ``summary`` line for list endpoints in the generated OpenAPI spec.
          Example: ``get_many_summary = "List all books"`` produces that phrase on ``GET /books``.
          Useful for clarifying collection responses at a glance.
    * - ``GET_SINGLE_SUMMARY``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Defines the doc summary for single-item ``GET`` requests.
          ``get_single_summary = "Fetch one book by ID"`` would appear beside ``GET /books/{id}``.
          Helps consumers quickly grasp endpoint intent.
    * - ``POST_SUMMARY``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Short line describing the create operation in documentation.
          For instance, ``post_summary = "Create a new book"`` labels ``POST /books`` accordingly.
          Particularly handy when auto-generated names need clearer wording.
    * - ``PATCH_SUMMARY``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Sets the summary for ``PATCH`` endpoints used in the OpenAPI docs.
          Example: ``patch_summary = "Update selected fields of a book"``.
          Provides readers with a concise explanation of partial updates.

