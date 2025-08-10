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


In `flarchitect`, configuration options play a crucial role in customizing the behavior of API and its accompanying
documentation. These configurations can be specified through `Flask`_ config values or directly within `SQLAlchemy`_ model
classes using `Meta` classes.

`Flask`_ config values are the most straightforward way to configure the API. Offering a standardized approach to modifying
the extension's behavior at a global or model level.




Config Hierarchy
--------------------------------



To offer flexibility and control, ``flarchitect`` adheres to a hierarchy of configuration priorities.

- Lowest Priority - At the base of this hierarchy are the global `Flask`_ config options, applied globally to all requests. These values will
  be overridden by more specific configurations.

- Method based configurations can be applied to the global `Flask`_ config, allowing for more precise control over the
  behavior of the API in response to specific `HTTP method`_.

- Model based configurations can be embedded within `SQLAlchemy`_ model classes through `Meta` class attributes, allowing
  for more fine-grained control over the behavior of the API in response to specific models.

- Highest Priority - Finally the highest precedence is given to model-specific configurations suffixed with a `HTTP method`_, allowing for
  the most detailed customization of the API's behavior per model and `HTTP method`_.


.. note::

    When applying config values

    - Global `Flask`_ config values are prefixed with ``API_``.
    - Global `Flask`_ method based config values are prefixed with ``API_{method}_``.
    - `SQLAlchemy`_ Model config values omit the ``API_`` prefix and are lower case.
    - `SQLAlchemy`_ Model method based config values omit the ``API_`` prefix, are lower case and are prefixed with the method.


.. note::

    Each configuration value below is assigned a tag, which will define where the value can be used and which priority
    it takes.

    Pri 1. :bdg-dark-line:`Model Method` - :doc:`View here<config_locations/model_method>`

    Pri 2. :bdg-dark-line:`Model` - :doc:`View here<config_locations/model>`

    Pri 3. :bdg-dark-line:`Global Method` - :doc:`View here<config_locations/global_method>`

    Pri 4. :bdg-dark-line:`Global` - :doc:`View here<config_locations/global_>`




Config Value Structure
--------------------------------

Every configuration value has a specific structure that defines where it can be used and how it should be written.
These are defined by the the below badges which are listed in the configuration value tables next to each value.

Please take note of the badge for each configuration value, as this will define where the value can be used and how it
should be written.



.. tab-set::

    .. tab-item:: Global

        :bdg-dark-line:`Global`

        Global configuration values are the lowest priority and apply to all requests unless overridden by a more specific
        configuration.

        They are applied in the `Flask`_. config class and are prefixed with ``API_``.

        Example `Flask`_ config value:

        .. code:: python

            class Config():

                TITLE="My API"

        See the :doc:`Global <config_locations/global_>` page for more information.

    .. tab-item:: Global Method

        :bdg-dark-line:`Global Method`

        Global configuration values can apply globally to specific `HTTP method`_, ``GET``, ``POST``, ``PUT``, ``DELETE``,
        ``PATCH``.

        The method should be added after the ``API_`` prefix.

        Example `Flask`_ config value:

        .. code:: python

            class Config():

                GET_RATE_LIMIT="100 per minute"
                POST_RATE_LIMIT="10 per minute"
                PATCH_RATE_LIMIT="10 per minute"

        See the :doc:`Global Method<config_locations/global_method>` page for more information.

    .. tab-item:: Model

        :bdg-dark-line:`Model`

        Model configuration values override any `Flask`_ configuration.

        They are applied in the `SQLAlchemy`_ models Meta class, they should omit the prefix ``API_`` and be written in lower
        case.

        Example model.Meta config value:

        .. code:: python

            class MyModel(db.model):
                __table__ = "my_model"

                class Meta:
                    # config value is shown as RATE_LIMIT in flask config
                    rate_limit = "10 per second"
                    # config value is shown as BLOCK_METHODS in flask config
                    blocked_methods = ["DELETE", "POST"]

        See the :doc:`Model<config_locations/model>` page for more information.


    .. tab-item:: Model Method


        :bdg-dark-line:`Model Method`

        Model method configuration values have the highest priority and will override any other configuration.

        They are applied in the `SQLAlchemy`_ models Meta class, they should omit the prefix ``API_``, be written in lower
        case and be prefixed with the method.

        Example model.Meta config value:

        .. code:: python

            class MyModel(db.model):
                __table__ = "my_model"

                class Meta:
                    # config value is shown as RATE_LIMIT in flask config
                    get_rate_limit = "10 per minute"
                    post_rate_limit = "5 per minute"

        See the :doc:`Model Method<config_locations/model_method>` page for more information.


Documentation Configuration Values
------------------------------------------


.. list-table::

    *
        - .. data:: CREATE_DOCS

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Controls whether the `Redoc`_ documentation is created and served by the API. When disabled, the API will
          not serve documentation. If true, the API will serve documentation at the url specified by `DOCUMENTATION_URL <configuration.html#DOCUMENTATION_URL>`_.
    *
        - .. data:: DOCUMENTATION_URL

          :bdg:`default:` ``/docs``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - The url for accessing the `ReDoc`_ documentation.
    *
        - .. data:: TITLE

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - Sets the title of your API in the generated ReDoc documentation. It appears prominently in the
          documentation, serving as a headline for users exploring your API.
    *
        - .. data:: VERSION

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - Sets the version number of your API. This value will appear in the generated ReDoc documentation and in api
          responses when `DUMP_VERSION` is enabled.

          Example:
            ``0.1.0``
    *
        - .. data:: LOGO_URL

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - When defined, a logo will be displayed in the ReDoc documentation. This should be be valid image URL
    *
        - .. data:: LOGO_BACKGROUND

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Paired with `LOGO_URL <configuration.html#LOGO_URL>`_, this value sets the background color of the logo in the ReDoc documentation.
          This value should be a valid CSS color value.

    *
        - .. data:: DESCRIPTION

          :bdg:`default:` ``./flask_schema/html/base_readme.MD``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - The main description of the API in the generated ReDoc documentation. This value should be a valid markdown
          string or a path to a markdown file. The file will be rendered with `Jinja`_ and you can access the `Flask`_
          config with the ``{{ config }}`` variable.

          -----------------------------------------------------------------

          View the template file `here <https://github.com/arched-dev/flarchitect/blob/master/flask_schema/html/base_readme.MD>`_

    *
        - .. data:: CONTACT_NAME

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Specifies the contact name for inquiries and support in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.
    *
        - .. data:: CONTACT_EMAIL

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Specifies the contact email for inquiries and support in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.
    *
        - .. data:: CONTACT_URL

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Specifies the contact web address for inquiries and support in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.
    *
        - .. data:: LICENCE_NAME

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Specifies the licence type for the API in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.
    *
        - .. data:: LICENCE_URL

          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - Specifies a url to the licence type for the API in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.
    *
        - .. data:: SERVER_URLS

          :bdg:`default:` ``None``

          :bdg:`type` ``list[dict]``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Specifies the server(s) used for calling the API in the `ReDoc`_ documentation. If not provided, the field name will not be displayed in the docs.

          Example structure:

            [{"url": "https://api.example.com", "description": "Main server"}, ...]

    *
        - .. data:: DOC_HTML_HEADERS


          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Custom CSS or JS to be added to the header of the `ReDoc`_ documentation HTML page.

          Example:

          .. code:: html

            <style>
                .redoc-section h1 {
                    color: red;
                }
            </style>
    *
        - .. data:: DOC_HTML_FOOTERS


          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Custom CSS or JS to be added to the footer of the `ReDoc`_ documentation HTML page.

          Example:

          .. code:: html

            <script src="https://my.script/main.js"></script>



    *
        - .. data:: VERBOSITY_LEVEL


          :bdg:`default:` ``0``

          :bdg:`type` ``int``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`


        - Controls the verbosity of **flarchitect**'s output to console, choose a value between 0 and 4.
          0 being no output and 4 being the most verbose.




API Configuration Values (MAIN)
------------------------------------------

.. list-table::

    *
        - .. data:: XML_AS_TEXT

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - For legacy systems XML can be output, if you need the response to be `text/xml` rather than `application/json`
          set this value to ``True``.

    *
        - .. data:: PRINT_EXCEPTIONS

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will print exceptions to the console when they occur. This is useful for debugging
          purposes.

    *
        - .. data:: DUMP_DATETIME

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``datetime`` field in the response data. This field will contain the
          current date and time of the response.
    *
        - .. data:: DUMP_VERSION

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``version`` field in the response data. This field will contain the
          version number of the API.
    *
        - .. data:: DUMP_STATUS_CODE

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``statusCode`` field in the response data. This field will contain the
          status code of the response.

          The output key will either be camelCase or snake_case depending on the value of `CONVERT_TO_CAMEL_CASE <configuration.html#CONVERT_TO_CAMEL_CASE>`_.
    *
        - .. data:: DUMP_RESPONSE_TIME

          :bdg:`default:` ``True``

          :bdg:`type` ``bool```

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``responseTime`` field in the response data. This field will contain the
          time taken to process the request in ms.

          The output key will either be camelCase or snake_case depending on the value of `CONVERT_TO_CAMEL_CASE <configuration.html#CONVERT_TO_CAMEL_CASE>`_.



    *
        - .. data:: DUMP_COUNT

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``totalCount`` field in the response data. This field will contain the
          total number of records available to be queried with pagination (not the number of records returned in the
          response).

          The output key will either be camelCase or snake_case depending on the value of `CONVERT_TO_CAMEL_CASE <configuration.html#CONVERT_TO_CAMEL_CASE>`_.

    *
        - .. data:: DUMP_NULL_NEXT_URL

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``nextUrl`` field in the response data if null. When disabled the
          ``nextUrl`` field will not be included in the response data if null.

          The output key will either be camelCase or snake_case depending on the value of `CONVERT_TO_CAMEL_CASE <configuration.html#CONVERT_TO_CAMEL_CASE>`_.


    *
        - .. data:: DUMP_NULL_PREVIOUS_URL

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``previousUrl`` field in the response data if null. When disabled the
          ``previousUrl`` field will not be included in the response data if null.

          The output key will either be camelCase or snake_case depending on the value of `CONVERT_TO_CAMEL_CASE <configuration.html#CONVERT_TO_CAMEL_CASE>`_.
    *
        - .. data:: DUMP_NULL_ERRORS

          :bdg:`default:` ``False``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``error`` field in the response data if null. When disabled the
          ``error`` field will not be included in the response data if null.


    *
        - .. data:: BASE_MODEL

          :bdg:`default:` ``None``

          :bdg:`type` ``DeclarativeBase``

          :bdg-danger:`Required` :bdg-dark-line:`Global`

        - The base class for all models in the API, and a required configuration value. Used by **flarchitect** to
          correctly analyse models and automatically create endpoints.

            This value should be a valid base model (`see here <https://docs.sqlalchemy.org/en/20/orm/quickstart.html#declare-models>`_).

          When using `Flask-SQLAlchemy`_ you must subclass your models with ``db.Model`` as normal, and also
          populate this field with ``db.Model``. You will, however, have to pass your actual base model to the
          ``SQLAlchemy.init_app(base_clas=YourBase)``

            View the :doc:`Quickstart <quickstart>` docs for more information on how to use this value.



    *
        - .. data:: DUMP_HYBRID_PROPERTIES

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - When enabled, the API will include hybrid properties in resources response data & in the `ReDoc`_
          documentation.


    *
        - .. data:: ADD_RELATIONS

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model`

        - When enabled, the API will automatically add relationships to the model's schema. This is useful for
          automatically including related resources in the response data.

    *
        - .. data:: IGNORE_UNDERSCORE_ATTRIBUTES

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - When enabled, the API will ignore all attributes that start with an underscore in the model. This is useful
          for hiding private attributes from the API.

    *
        - .. data:: PAGINATION_SIZE_DEFAULT

          :bdg:`default:` ``20``

          :bdg:`type` ``int``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - The default number of records to return in a single response. This value can be overridden by the client
          by adding the query parameter ``?limit=`` to the request. The maximum value for this parameter is defined by
          `PAGINATION_SIZE_MAX <configuration.html#PAGINATION_SIZE_MAX>`_.

    *
        - .. data:: PAGINATION_SIZE_MAX

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - The maximum number of records to return in a single response. The default (no query parameter) is defined by
          `PAGINATION_SIZE_DEFAULT <configuration.html#PAGINATION_SIZE_DEFAULT>`_. Adding the query parameter
          ``?limit=`` to the request allows the user in increase this default but it is limited to this value as the
          maximum allowed to be returned. Increase this value to allow more records to be returned in a single response.


API Callbacks
------------------------------------------

.. list-table::




    *
        - .. data:: SETUP_CALLBACK

          :bdg:`default:` ``None``

          :bdg:`type` ``callable``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - When assigned, the API will call the function prior to the model being queried.
          This is useful for adding custom logic to the API, such as adding additional query parameters/modifying the
          query or logging request to the database.

            View an example function & its signature `here <callbacks.html#setup-function-signature>`_.
    *
        - .. data:: POST_DUMP_CALLBACK

          :bdg:`default:` ``None``

          :bdg:`type` ``callable``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - When assigned, the API will call the function after the model has been dumped to a dictionary by Marshmallow.
          Its possible to add extra validation here or modify the response data.

          View an example function & its signature `here <callbacks.html#post-dump-function-signature>`_.

    *
        - .. data:: RETURN_CALLBACK

          :bdg:`default:` ``None``

          :bdg:`type` ``callable``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - When assigned, the API will call the function post database call and pre returning
          the data to the client. This is useful for adding custom logic to the API, such as modifying the response data
          or logging the response to the database.

            View an example function & its signature `here <callbacks.html#return-function-signature>`_.

    *
        - .. data:: ERROR_CALLBACK

          :bdg:`default:` ``None``

          :bdg:`type` ``callable``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global Method`

        - When assigned, the API will call the function when an error occurs. This is useful
          for adding custom logic to the API, such as logging the error to the database, sending an emails etc.

            View an example function & its signature `here <callbacks.html#error-function-signature>`_.

    *
        - .. data:: ADDITIONAL_QUERY_PARAMS

          :bdg:`default:` ``None``

          :bdg:`type` ``list[dict]``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - If you are hoping to extend the default query parameters of the API using callbacks, you may also want to add
          these to the `ReDoc`_ documentation. This value allows you to add additional query parameters per model or
          globally to the API.

            View an example of its use and expected value here `Example of its use here <configuration.html#extending-query-params>`_.


API Method Config (Delete)
------------------------------------------

.. list-table::


    *
        - .. data:: ALLOW_DELETE_RELATED

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - When enabled, the API will allow the user to specify models to delete along with the model being queried.

            i.e ``?delete_related=Books,Authors``

          When disabled, the API will not allow these operations and will raise a 409 error if the user attempts to do
          so, signalling that the operation is not allowed along with a message of the offending related model(s).

          .. note::

            Setting the cascade delete options on your models, is the best way to control this behavior.
    *
        - .. data:: ALLOW_DELETE_DEPENDENTS

          :bdg:`default:` ``True``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Model Method`

        - When enabled, the API will recursively attempt to delete all dependents of the model being queried.

            i.e ``?delete_dependents=1``

          Its possible however, some fringe cases have not been accounted for and the operation may fail. In this case
          it is always best to set the cascade delete options on your models to control this behavior.

          When disabled, the API will not allow these operations and will raise a 400 error if the user attempts to apply
          the query parameter.

          .. note::

            Setting the cascade delete options on your models, is the best way to control this behavior.
    *
        - .. data::  SOFT_DELETE


          :bdg:`default:` ``False``

          :bdg:`type` ``bool``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will soft delete records from the database. Soft deleting will mark a record as deleted
          in a user specified column, rather than actually deleting the record from the database. Users can show deleted
          records with the query parameter ``?include_deleted=true``. Relies on `SOFT_DELETE_ATTRIBUTE <configuration.html#SOFT_DELETE_ATTRIBUTE>`_ and `SOFT_DELETE_VALUES <configuration.html#SOFT_DELETE_VALUES>`_ to function.

    *
        - .. data::  SOFT_DELETE_ATTRIBUTE


          :bdg:`default:` ``None``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - The model attribute name that hold the soft delete value. This value should be ideally set in your base model
          and can be any type, but for ease boolean is recommended. i.e  ``deleted`` for the attribute name with a default
          value of ``False``. Active and deleted values can be set in `SOFT_DELETE_VALUES <configuration.html#SOFT_DELETE_VALUES>`_.

    *
        - .. data::  SOFT_DELETE_VALUES


          :bdg:`default:` ``None``

          :bdg:`type` ``tuple``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - A tuple that represents the ``Active`` and ``Deleted`` values for the `SOFT_DELETE_ATTRIBUTE <configuration.html#SOFT_DELETE_ATTRIBUTE>`_.
          i.e ``(False, True)`` or ``("active", "deleted")``.

Schema Configuration Values
------------------------------------------

.. list-table::

    *
        - .. data:: BASE_SCHEMA

          :bdg:`default:` ``AutoSchema``

          :bdg:`type` ``Schema``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - At the heart of **flarchitect** is the ``AutoSchema`` which creates and translates your `SQLAlchemy`_ models
          into `Marshmallow`_ schema's. This value should be a valid schema class (`see here <https://marshmallow.readthedocs.io/en/stable/quickstart.html>`_).

            It is advisable to leave this value as the default, unless you have a specific use case or know what you
            are doing.



    *
        - .. data:: ENDPOINT_CASE

          :bdg:`default:` ``kebab``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - One of the following options: ``camel``, ``pascal``, ``snake``, ``screaming_snake``, ``kebab`` or ``screaming_kebab``.

          Defines which case to use to convert the model names into endpoint URLs. To keep inline with restful API
          conventions, the endpoint URL will also be pluralized.

    *
        - .. data:: FIELD_CASE

          :bdg:`default:` ``snake``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - One of the following options: ``camel``, ``pascal``, ``snake``, ``screaming_snake``, ``kebab``,
          ``screaming_kebab``. This value will be used to convert the model attributes into field names.

    *
        - .. data:: SCHEMA_CASE

          :bdg:`default:` ``camel``

          :bdg:`type` ``str``

          :bdg-secondary:`Optional` :bdg-dark-line:`Global`

        - When enabled, the API will include a ``datetime`` field in the response data. This field will contain the
          current date and time of the response.
