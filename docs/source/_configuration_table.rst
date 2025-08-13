.. list-table::

    * - ``API_CREATE_DOCS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Controls whether ReDoc documentation is generated automatically. Set to ``False`` to disable docs in production or when using an external documentation tool. Accepts ``True`` or ``False``. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DOCUMENTATION_URL``

          :bdg:`default:` ``/docs``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - URL path where documentation is served. Useful for mounting docs under a custom route such as ``/redoc``. Accepts any valid path string. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_TITLE``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - Sets the display title of the generated documentation. Provide a concise project name or API identifier. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_VERSION``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - Defines the version string shown in the docs header, helping consumers track API revisions. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_LOGO_URL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - URL or path to an image used as the documentation logo. Useful for branding or product recognition. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_LOGO_BACKGROUND``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Sets the background colour behind the logo, allowing alignment with corporate branding. Accepts any CSS colour string. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DESCRIPTION``

          :bdg:`type` ``str or str path``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Accepts free text or a filepath to a Jinja template and supplies the description shown on the docs landing page. Useful for providing an overview or dynamically generated content using ``{config.xxxx}`` placeholders. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_KEYWORDS``

          :bdg:`default:` ``None``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Comma-separated keywords that improve searchability and SEO of the documentation page. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_CONTACT_NAME``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Human-readable name for API support or maintainer shown in the docs. Leave ``None`` to omit the contact block. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_CONTACT_EMAIL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Email address displayed for support requests. Use when consumers need a direct channel for help. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_CONTACT_URL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Website or documentation page for further assistance. Set to ``None`` to hide the link. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_LICENCE_NAME``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Name of the licence governing the API, e.g., ``MIT`` or ``Apache-2.0``. Helps consumers understand usage rights. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_LICENCE_URL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - URL linking to the full licence text for transparency. Set to ``None`` to omit. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SERVER_URLS``

          :bdg:`default:` ``None``
          :bdg:`type` ``list[dict]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - List of server objects defining environments where the API is hosted. Each dict may include ``url`` and ``description`` keys. Ideal for multi-environment setups. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DOC_HTML_HEADERS``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - HTML ``<head>`` snippets inserted into the documentation page. Use to add meta tags or analytics scripts. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DOC_HTML_FOOTERS``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - HTML ``<footer>`` snippets rendered at the bottom of the docs page, useful for legal notices or navigation links.
    * - ``API_PREFIX``

          :bdg:`default:` ``/api``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Base path prefix applied to all API routes. Adjust when mounting the API under a subpath such as ``/v1``. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_VERBOSITY_LEVEL``

          :bdg:`default:` ``1``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Verbosity for console output during API generation. ``0`` silences logs while higher values provide more detail. Example: `tests/test_model_meta/model_meta/config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_model_meta/model_meta/config.py>`_.
    * - ``API_ENDPOINT_CASE``

          :bdg:`default:` ``kebab``
          :bdg:`type` ``string``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Case style for generated endpoint URLs such as ``kebab`` or ``snake``. Choose to match your project's conventions. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_FIELD_CASE``

          :bdg:`default:` ``snake``
          :bdg:`type` ``string``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Determines the case used for field names in responses, e.g., ``snake`` or ``camel``. Helps integrate with client expectations. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SCHEMA_CASE``

          :bdg:`default:` ``camel``
          :bdg:`type` ``string``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Naming convention for generated schemas. Options include ``camel`` or ``snake`` depending on tooling preferences. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_PRINT_EXCEPTIONS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Toggles Flask's exception printing in responses. Disable in production for cleaner error messages. Options: ``True`` or ``False``.
    * - ``API_BASE_SCHEMA``

          :bdg:`default:` ``AutoSchema``
          :bdg:`type` ``Schema``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Base schema class used for model serialization. Override with a custom schema to adjust marshmallow behaviour. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ALLOW_CASCADE_DELETE``

          :bdg-secondary:`Optional` 

        - Allows cascading deletes on related models when a parent is removed. Use with caution to avoid accidental data loss. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_IGNORE_UNDERSCORE_ATTRIBUTES``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Ignores attributes prefixed with ``_`` during serialization to keep internal fields hidden. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SERIALIZATION_TYPE``

          :bdg-secondary:`Optional` 

        - Output format for serialized data, such as ``json`` or ``xml``. Determines how responses are rendered. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SERIALIZATION_DEPTH``

          :bdg-secondary:`Optional` 

        - Depth for nested relationship serialization. Higher numbers include deeper related objects, impacting performance.
    * - ``API_DUMP_HYBRID_PROPERTIES``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Includes hybrid SQLAlchemy properties in serialized output. Disable to omit computed attributes. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ADD_RELATIONS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Adds relationship fields to serialized output, enabling nested data representation. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_PAGINATION_SIZE_DEFAULT``

          :bdg:`default:` ``20``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Default number of items returned per page when pagination is enabled. Set lower for lightweight responses. Example: `tests/test_api_filters.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_api_filters.py>`_.
    * - ``API_PAGINATION_SIZE_MAX``

          :bdg:`default:` ``100``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Maximum allowed page size to prevent clients requesting excessive data. Adjust based on performance considerations.
    * - ``API_READ_ONLY``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - When ``True``, only read operations are allowed on models, blocking writes for safety. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ALLOW_ORDER_BY``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Enables ``order_by`` query parameter to sort results. Disable to enforce fixed ordering. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ALLOW_FILTER``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Allows filtering using query parameters. Useful for building rich search functionality. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ALLOW_JOIN``

          :bdg-secondary:`Optional` 

        - Intended toggle for joining related models in queries. Currently not implemented.
    * - ``API_ALLOW_GROUPBY``

          :bdg-secondary:`Optional` 

        - Placeholder for future group-by functionality in query parameters.
    * - ``API_ALLOW_AGGREGATION``

          :bdg-secondary:`Optional` 

        - Reserved for upcoming aggregation features in API queries.
    * - ``API_ALLOW_SELECT_FIELDS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Allows clients to specify which fields to return, reducing payload size. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_block_methods``

          :bdg-secondary:`Optional` 

        - List of HTTP methods to block for this API, such as ``["DELETE", "POST"]``. Useful for read-only endpoints.
    * - ``API_AUTHENTICATE``

          :bdg-secondary:`Optional` 

        - Enables authentication on all routes. When provided, requests must pass the configured authentication check. Example: `tests/test_authentication.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_authentication.py>`_.
    * - ``API_AUTHENTICATE_METHOD``

          :bdg-secondary:`Optional` 

        - Name of the authentication method used, such as ``jwt`` or ``basic``. Determines which auth backend to apply. Example: `tests/test_authentication.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_authentication.py>`_.
    * - ``API_USER_MODEL``

          :bdg-secondary:`Optional` 

        - Import path for the user model leveraged during authentication workflows. Example: `tests/test_authentication.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_authentication.py>`_.
    * - ``API_SETUP_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Function executed before processing a request, ideal for setup tasks or validation. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_RETURN_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Callback invoked to modify the response payload before returning it to the client. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ERROR_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Error-handling hook allowing custom formatting or logging of exceptions. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_POST_DUMP_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Post-serialization hook to further transform or audit the output data before it is returned.
    * - ``API_ADDITIONAL_QUERY_PARAMS``

          :bdg:`default:` ``None``
          :bdg:`type` ``list[dict]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Extra query parameters supported by the endpoint. Each dict may contain ``name`` and ``schema`` keys. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_DATETIME``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Appends the current UTC timestamp to responses for auditing. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_VERSION``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Includes the API version string in every payload. Helpful for client-side caching. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_STATUS_CODE``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Adds the HTTP status code to the serialized output, clarifying request outcomes. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_RESPONSE_TIME``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Adds the elapsed processing time in milliseconds to the response, enabling performance monitoring.
    * - ``API_DUMP_COUNT``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Includes the total count of items returned, aiding pagination UX.
    * - ``API_DUMP_NULL_NEXT_URL``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When pagination reaches the end, returns ``null`` for ``next`` URLs instead of omitting the key. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_NULL_PREVIOUS_URL``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Ensures ``previous`` URLs are present even when no prior page exists by returning ``null``. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_NULL_ERROR``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Provides a consistent ``error`` field in responses, defaulting to ``null`` when no error occurred. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_RATE_LIMIT``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Rate limit string using Flask-Limiter syntax (e.g., ``100/minute``) to throttle requests. Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_RATE_LIMIT_CALLBACK``

          :bdg-secondary:`Optional` 

        - Custom callback executed when a rate limit is hit, enabling logging or alternative responses.
    * - ``API_RATE_LIMIT_STORAGE_URI``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Storage backend for rate limit data such as ``redis://`` or ``memory://``.
    * - ``IGNORE_FIELDS``

          :bdg-secondary:`Optional` 

        - Fields to exclude entirely from both input and output payloads.
    * - ``IGNORE_OUTPUT_FIELDS``

          :bdg-secondary:`Optional` 

        - Fields removed from output serialization while still accepted on input.
    * - ``IGNORE_INPUT_FIELDS``

          :bdg-secondary:`Optional` 

        - Input-only fields stripped from response bodies but required on create or update.
    * - ``API_BLUEPRINT_NAME``

          :bdg:`default:` ``None``
          :bdg-secondary:`Optional` 

        - Name given to the Flask blueprint that houses the API routes. Useful for namespacing.
    * - ``API_SOFT_DELETE``

          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Enables soft deletion by marking records instead of removing them. Pair with corresponding attribute and values. Example: `demo/soft_delete/soft_delete/config.py <https://github.com/arched-dev/flarchitect/blob/master/demo/soft_delete/soft_delete/config.py>`_.
    * - ``API_SOFT_DELETE_ATTRIBUTE``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Column name used to flag soft-deleted records, e.g., ``status``. Example: `demo/soft_delete/soft_delete/config.py <https://github.com/arched-dev/flarchitect/blob/master/demo/soft_delete/soft_delete/config.py>`_.
    * - ``API_SOFT_DELETE_VALUES``

          :bdg:`default:` ``None``
          :bdg:`type` ``tuple``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Tuple of values representing active and deleted states, such as ``("active", "deleted")``. Example: `demo/soft_delete/soft_delete/config.py <https://github.com/arched-dev/flarchitect/blob/master/demo/soft_delete/soft_delete/config.py>`_.
    * - ``API_ALLOW_DELETE_RELATED``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Allows removal of related records when a parent is deleted. Disable to enforce manual cleanup.
    * - ``API_ALLOW_DELETE_DEPENDENTS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Permits deletion of dependent objects that rely on the target record.
    * - ``GET_MANY_SUMMARY``

          :bdg-secondary:`Optional` 

        - Short description for list endpoints used in generated docs.
    * - ``GET_SINGLE_SUMMARY``

          :bdg-secondary:`Optional` 

        - Summary shown in docs for retrieving a single record.
    * - ``POST_SUMMARY``

          :bdg-secondary:`Optional` 

        - Brief explanation of the create operation in documentation.
    * - ``PATCH_SUMMARY``

          :bdg-secondary:`Optional` 

        - Short description for partial update operations.
