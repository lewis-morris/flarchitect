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

In `flarchitect`, configuration options are essential for customizing the API and its accompanying documentation.
These settings can be provided through `Flask`_ config values or directly within `SQLAlchemy`_ model classes using ``Meta`` classes.

Beyond the basics, the extension supports hooks and advanced flags for post-serialization callbacks, rate limiting, field exclusion, blueprint naming, soft deletion, and per-method documentation summaries.

`Flask`_ config values offer a straightforward, standardized way to modify the extension's behavior at a global or model level.

Config Hierarchy
--------------------------------

To offer flexibility and control, **flarchitect** follows a hierarchy of configuration priorities:

- **Lowest Priority** – Global `Flask`_ config options apply to all requests and are overridden by any more specific configuration.
- **Method-based** – Method-specific options can override global settings for particular HTTP methods.
- **Model-based** – `SQLAlchemy`_ model ``Meta`` attributes override both global and method-based configurations.
- **Highest Priority** – Model-specific configurations suffixed with an `HTTP method`_ allow the most detailed customization per model and method.

.. note::

    When applying config values:

    - Global `Flask`_ config values are prefixed with ``API_``.
    - Global method-based `Flask`_ config values are prefixed with ``API_{method}_``.
    - `SQLAlchemy`_ model config values omit the ``API_`` prefix and are lowercase.
    - `SQLAlchemy`_ model method config values omit the ``API_`` prefix, are lowercase, and are prefixed with the method.

.. note::

    Each configuration value below is assigned a tag, which defines where the value can be used and its priority:

    Pri 1. :bdg-dark-line:`Model Method` - :doc:`View here<config_locations/model_method>`

    Pri 2. :bdg-dark-line:`Model` - :doc:`View here<config_locations/model>`

    Pri 3. :bdg-dark-line:`Global Method` - :doc:`View here<config_locations/global_method>`

    Pri 4. :bdg-dark-line:`Global` - :doc:`View here<config_locations/global_>`

Config Value Structure
--------------------------------

Every configuration value has a specific structure that defines where it can be used and how it should be written.  
These structures are indicated by the badges in the configuration tables next to each value.

Please note the badge for each configuration value, as it defines where the value can be used and how it should be written.

.. tab-set::

    .. tab-item:: Global

        :bdg-dark-line:`Global`

        Global configuration values are the lowest priority and apply to all requests unless overridden by a more specific configuration.

        They are applied in the `Flask` config object and are prefixed with ``API_``.

        These settings are ideal for defining application-wide defaults such as API metadata, documentation behaviour,
        or pagination policies. Any option listed in the configuration table can be supplied here using its
        global ``API_`` form (for example ``API_TITLE`` or ``API_PREFIX``) and may accept strings, integers,
        booleans, lists, or dictionaries depending on the option.

        Use this level when you need a single setting to apply consistently across all models and methods.

        Example:

        .. code:: python

            class Config:
                API_TITLE = "My API"

        See the :doc:`Global <config_locations/global_>` page for more information.

    .. tab-item:: Global Method

        :bdg-dark-line:`Global Method`

        Global configuration values can apply to specific HTTP methods: ``GET``, ``POST``, ``PUT``, ``DELETE``, or ``PATCH``.

        The method name should be added after the ``API_`` prefix.

        Use method-scoped options to change behaviour between reads and writes across the entire API, such as
        applying tighter rate limits to mutating requests or disabling a verb globally. Any global configuration
        key that supports method scoping can be used here by inserting the method name (e.g. ``API_GET_RATE_LIMIT``),
        with value types mirroring their global counterparts.

        Example:

        .. code:: python

            class Config:
                API_GET_RATE_LIMIT = "100 per minute"
                API_POST_RATE_LIMIT = "10 per minute"
                API_PATCH_RATE_LIMIT = "10 per minute"

        See the :doc:`Global Method<config_locations/global_method>` page for more information.

    .. tab-item:: Model

        :bdg-dark-line:`Model`

        Model configuration values override any global `Flask`_ configuration.

        They are applied in the `SQLAlchemy`_ model's ``Meta`` class, omit the ``API_`` prefix, and are written in lowercase.

        Configure this level when a single model requires behaviour different from the rest of the application,
        such as marking a model read only, changing its serialization depth, or blocking specific methods.
        Options correspond directly to the global keys but in lowercase without the prefix (for example ``rate_limit``
        or ``pagination_size_default``) and accept the same data types noted in the configuration table.

        Example:

        .. code:: python

            class MyModel(db.Model):
                __tablename__ = "my_model"

                class Meta:
                    rate_limit = "10 per second"        # shown as API_RATE_LIMIT in Flask config
                    blocked_methods = ["DELETE", "POST"]  # shown as API_BLOCK_METHODS in Flask config

        See the :doc:`Model<config_locations/model>` page for more information.

    .. tab-item:: Model Method

        :bdg-dark-line:`Model Method`

        Model method configuration values have the highest priority and override all other configuration.

        They are applied in the `SQLAlchemy`_ model's ``Meta`` class, omit the ``API_`` prefix, are lowercase, and are prefixed with the method.

        Use these settings to fine-tune behaviour for a specific model-method combination. This is useful when,
        for example, a model should allow ``GET`` requests with a high rate limit but restrict ``POST`` calls or
        customise serialization only for ``PATCH``. Any model-level option can be adapted by prefixing it with the
        HTTP method name (such as ``get_rate_limit`` or ``post_blocked``) and follows the same value types as the
        corresponding model option.

        Example:

        .. code:: python

            class MyModel(db.Model):
                __tablename__ = "my_model"

                class Meta:
                    get_rate_limit = "10 per minute"   # shown as API_GET_RATE_LIMIT in Flask config
                    post_rate_limit = "5 per minute"   # shown as API_POST_RATE_LIMIT in Flask config

        See the :doc:`Model Method<config_locations/model_method>` page for more information.


Cascade delete settings
-----------------------

See :ref:`cascade-deletes` in the advanced configuration guide for usage examples of
:data:`API_ALLOW_CASCADE_DELETE`, :data:`API_ALLOW_DELETE_RELATED` and
:data:`API_ALLOW_DELETE_DEPENDENTS`.


Complete Configuration Reference
--------------------------------

.. include:: _configuration_table.rst
