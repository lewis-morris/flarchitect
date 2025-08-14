FAQ
=========================================


.. dropdown:: Can I change the case of the output?


    Be default url endpoints are ``pluralized kebab-case``, resources are ``camelCase`` and resource fields are
    ``snake_case``.

    You can change the default behaviour easily by adding the below global flask configurations:

        `API_ENDPOINT_CASE <configuration.html#ENDPOINT_CASE>`_

        `API_FIELD_CASE <configuration.html#FIELD_CASE>`_

        `API_SCHEMA_CASE <configuration.html#SCHEMA_CASE>`_

    Options are: camel, pascal, snake, kebab, screaming_kebab, screaming_snake


.. dropdown:: Can I block http methods in my API?


    `Http method`_'s can be blocked easily, on a global or a model level. See here for full information on how to block
    methods.

        `API_BLOCK_METHODS <configuration.html#BLOCK_METHODS>`_

    Example blocking all ``DELETE`` & ``POST`` methods:


    .. code-block:: python

        app.config['API_BLOCK_METHODS'] = ['DELETE', 'POST]


    Example blocking ``DELETE`` & ``POST`` methods on a specific model:

    .. code-block:: python

        class MyModel(Model):
            class Meta:
                block_methods = ['DELETE', 'POST']


    Alternatively, If you want to only allow ``GET`` requests you can turn on the
    `API_READ_ONLY <configuration.html#READ_ONLY>`_ option in the `Flask`_ configuration, which will block all but ``GET``
    requests from being served.


.. dropdown:: Can I extend the functionality of the API?


    If you need to perform some custom logic or actions, you can use callbacks. Callbacks are functions
    that fire:

    - before the database query is performed
    - before the data is returned to the api
    - on an exception being raised

    See the below configuration values that can be defined globally as `Flask`_ configurations or on a model level.

        `API_SETUP_CALLBACK <configuration.html#SETUP_CALLBACK>`_

        `API_RETURN_CALLBACK <configuration.html#RETURN_CALLBACK>`_

        `API_ERROR_CALLBACK <configuration.html#ERROR_CALLBACK>`_


.. dropdown:: I use soft deletes, what can I do?


    If you need to perform soft deletes, you can use the `API_SOFT_DELETE <configuration.html#SOFT_DELETE>`_ configuration
    as a `Flask`_ global configuration. See :ref:`soft-delete` for an example.

    Additonal configuration values to set the attribute that holds the delete flag and the value that represents the
    ``active`` and ``deleted`` value is also needed.

    See the below configuration values that can be defined globally as `Flask`_ configurations or on a model level.

        `API_SOFT_DELETE_ATTRIBUTE <configuration.html#SOFT_DELETE_ATTRIBUTE>`_

        `API_SOFT_DELETE_VALUES <configuration.html#SOFT_DELETE_VALUES>`_

.. dropdown:: Can I generate an OpenAPI specification document?

    Yes. When ``API_CREATE_DOCS`` is enabled the schema is automatically
    generated at start-up and served at ``/openapi.json``. See
    :doc:`openapi` for examples on exporting or customising the document.

.. dropdown:: How do I update documentation after adding new models?

    Restart your application. The specification is rebuilt on boot and will
    include any newly registered models or routes.

Troubleshooting
---------------

.. dropdown:: The documentation endpoint returns 404

    Ensure ``API_CREATE_DOCS`` is set to ``True`` and that the
    :class:`flarchitect.Architect` has been initialised. If
    you mount the app under a prefix, check ``documentation_url_prefix``.

.. dropdown:: A route is missing from the spec

    Confirm the model has a ``Meta`` class and the endpoint isn't blocked by
    ``API_BLOCK_METHODS``. Rebuilding the application will refresh the
    specification.
