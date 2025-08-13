.. list-table::

    * - ``API_CREATE_DOCS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DOCUMENTATION_URL``

          :bdg:`default:` ``/docs``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - The url of the docs  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_TITLE``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - The title of the docs  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_VERSION``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - The version no of the docs  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_LOGO_URL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - The logo to display in the docs  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_LOGO_BACKGROUND``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - The background colour of the area where the logo is  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DESCRIPTION``

          :bdg:`type` ``str or str path``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Accepts a string or a filepath string, with a default behavior that auto-generates a comprehensive documentation description.   If a filepath is provided, it can point to a Jinja template that dynamically accesses the Flask configuration via {config.xxxx} placeholders. This flexible approach allows for a rich, context-aware description in your ReDoc documentation.  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_KEYWORDS``

          :bdg:`default:` ``None``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - 
    * - ``API_CONTACT_NAME``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Specifies the contact name for inquiries and support in the redoc documentation. If not provided, the field name will not be displayed in the docs.  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_CONTACT_EMAIL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Specifies the contact email for inquiries and support in the redoc documentation. If not provided, the field name will not be displayed in the docs.  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_CONTACT_URL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Specifies the contact url for inquiries and support in the redoc documentation. If not provided, the field name will not be displayed in the docs.  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_LICENCE_NAME``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Specifies the licence name in the redoc documentation. If not provided, the field name will not be displayed in the docs.  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_LICENCE_URL``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Specifies the licence url in the redoc documentation. If not provided, the field name will not be displayed in the docs.  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SERVER_URLS``

          :bdg:`default:` ``None``
          :bdg:`type` ``list[dict]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - example: [{"url": "http://localhost:5000", "description": "Local server"}...]  Specifies the server(s) used for   calling the API in the redoc documentation. If not provided, the field name will not be displayed in the docs.  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DOC_HTML_HEADERS``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - custom headers to be added to the documentation page.  Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DOC_HTML_FOOTERS``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - custom footers to be added to the documentation page.
    * - ``API_PREFIX``

          :bdg:`default:` ``/api``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_VERBOSITY_LEVEL``

          :bdg:`default:` ``1``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_model_meta/model_meta/config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_model_meta/model_meta/config.py>`_.
    * - ``API_ENDPOINT_CASE``

          :bdg:`default:` ``kebab``
          :bdg:`type` ``string``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_FIELD_CASE``

          :bdg:`default:` ``snake``
          :bdg:`type` ``string``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SCHEMA_CASE``

          :bdg:`default:` ``camel``
          :bdg:`type` ``string``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_PRINT_EXCEPTIONS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - 
    * - ``API_BASE_SCHEMA``

          :bdg:`default:` ``AutoSchema``
          :bdg:`type` ``Schema``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - 
    * - ``API_ALLOW_CASCADE_DELETE``

          :bdg-secondary:`Optional` 

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_IGNORE_UNDERSCORE_ATTRIBUTES``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SERIALIZATION_TYPE``

          :bdg-secondary:`Optional` 

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_SERIALIZATION_DEPTH``

          :bdg-secondary:`Optional` 

        - 
    * - ``API_DUMP_HYBRID_PROPERTIES``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ADD_RELATIONS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_PAGINATION_SIZE_DEFAULT``

          :bdg:`default:` ``20``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_api_filters.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_api_filters.py>`_.
    * - ``API_PAGINATION_SIZE_MAX``

          :bdg:`default:` ``100``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - 
    * - ``API_READ_ONLY``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ALLOW_ORDER_BY``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ALLOW_FILTER``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ALLOW_JOIN``

          :bdg-secondary:`Optional` 

        - IN DEVELOPMENT
    * - ``API_ALLOW_GROUPBY``

          :bdg-secondary:`Optional` 

        - IN DEVELOPMENT
    * - ``API_ALLOW_AGGREGATION``

          :bdg-secondary:`Optional` 

        - IN DEVELOPMENT
    * - ``API_ALLOW_SELECT_FIELDS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_block_methods``

          :bdg-secondary:`Optional` 

        - 
    * - ``API_AUTHENTICATE``

          :bdg-secondary:`Optional` 

        - Example: `tests/test_authentication.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_authentication.py>`_.
    * - ``API_AUTHENTICATE_METHOD``

          :bdg-secondary:`Optional` 

        - Example: `tests/test_authentication.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_authentication.py>`_.
    * - ``API_USER_MODEL``

          :bdg-secondary:`Optional` 

        - Example: `tests/test_authentication.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_authentication.py>`_.
    * - ``API_SETUP_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_RETURN_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_ERROR_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_POST_DUMP_CALLBACK``

          :bdg:`default:` ``None``
          :bdg:`type` ``callable``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - 
    * - ``API_ADDITIONAL_QUERY_PARAMS``

          :bdg:`default:` ``None``
          :bdg:`type` ``list[dict]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_DATETIME``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_VERSION``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_STATUS_CODE``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_RESPONSE_TIME``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - 
    * - ``API_DUMP_COUNT``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - 
    * - ``API_DUMP_NULL_NEXT_URL``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_NULL_PREVIOUS_URL``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_DUMP_NULL_ERROR``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_RATE_LIMIT``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - Example: `tests/test_flask_config.py <https://github.com/arched-dev/flarchitect/blob/master/tests/test_flask_config.py>`_.
    * - ``API_RATE_LIMIT_CALLBACK``

          :bdg-secondary:`Optional` 

        - 
    * - ``API_RATE_LIMIT_STORAGE_URI``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - 
    * - ``IGNORE_FIELDS``

          :bdg-secondary:`Optional` 

        - 
    * - ``IGNORE_OUTPUT_FIELDS``

          :bdg-secondary:`Optional` 

        - 
    * - ``IGNORE_INPUT_FIELDS``

          :bdg-secondary:`Optional` 

        - 
    * - ``API_BLUEPRINT_NAME``

          :bdg:`default:` ``None``
          :bdg-secondary:`Optional` 

        - 
    * - ``API_SOFT_DELETE``

          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `demo/soft_delete/soft_delete/config.py <https://github.com/arched-dev/flarchitect/blob/master/demo/soft_delete/soft_delete/config.py>`_.
    * - ``API_SOFT_DELETE_ATTRIBUTE``

          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `demo/soft_delete/soft_delete/config.py <https://github.com/arched-dev/flarchitect/blob/master/demo/soft_delete/soft_delete/config.py>`_.
    * - ``API_SOFT_DELETE_VALUES``

          :bdg:`default:` ``None``
          :bdg:`type` ``tuple``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Example: `demo/soft_delete/soft_delete/config.py <https://github.com/arched-dev/flarchitect/blob/master/demo/soft_delete/soft_delete/config.py>`_.
    * - ``API_ALLOW_DELETE_RELATED``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - 
    * - ``API_ALLOW_DELETE_DEPENDENTS``

          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - 
    * - ``GET_MANY_SUMMARY``

          :bdg-secondary:`Optional` 

        - 
    * - ``GET_SINGLE_SUMMARY``

          :bdg-secondary:`Optional` 

        - 
    * - ``POST_SUMMARY``

          :bdg-secondary:`Optional` 

        - 
    * - ``PATCH_SUMMARY``

          :bdg-secondary:`Optional` 

        - 
