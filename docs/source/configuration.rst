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

`Flask`_ config values offer a straightforward, standardized way to modify the extension's behavior at a global or model level.

Config Hierarchy
--------------------------------

To offer flexibility and control, **flarchitect** follows a hierarchy of configuration priorities:

- **Lowest Priority** – Global `Flask`_ config options apply to all requests and are overridden by any more specific configuration.
- **Method-based** – Method-specific options can override global settings for particular `HTTP method`_s.
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

        Example:

        .. code:: python

            class Config:
                API_TITLE = "My API"

        See the :doc:`Global <config_locations/global_>` page for more information.

    .. tab-item:: Global Method

        :bdg-dark-line:`Global Method`

        Global configuration values can apply to specific HTTP methods: ``GET``, ``POST``, ``PUT``, ``DELETE``, or ``PATCH``.

        The method name should be added after the ``API_`` prefix.

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

        Example:

        .. code:: python

            class MyModel(db.Model):
                __tablename__ = "my_model"

                class Meta:
                    get_rate_limit = "10 per minute"   # shown as API_GET_RATE_LIMIT in Flask config
                    post_rate_limit = "5 per minute"   # shown as API_POST_RATE_LIMIT in Flask config

        See the :doc:`Model Method<config_locations/model_method>` page for more information.

Documentation Configuration Values
-----------------------------------
.. list-table::

    * - .. data:: CREATE_DOCS
          :bdg:`default:` ``True``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Controls whether `ReDoc`_ documentation is created and served.  
          When ``False``, documentation is not served.  
          When ``True``, it is served at the URL set by :data:`DOCUMENTATION_URL`.

    * - .. data:: DOCUMENTATION_URL
          :bdg:`default:` ``/docs``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - The URL where `ReDoc`_ documentation is available.

    * - .. data:: TITLE
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-danger:`Required` :bdg-dark-line:`Global`
        - Sets the API title in generated documentation.

    * - .. data:: VERSION
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-danger:`Required` :bdg-dark-line:`Global`
        - Sets the API version. Appears in docs and API responses when :data:`DUMP_VERSION` is enabled.

    * - .. data:: LOGO_URL
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - URL of a logo to display in the documentation.

    * - .. data:: LOGO_BACKGROUND
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Background color for the logo in documentation.

    * - .. data:: DESCRIPTION
          :bdg:`default:` ``./flask_schema/html/base_readme.MD``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Main description for the API docs. Can be a markdown string or a path to a markdown file.  
          Markdown files are rendered with `Jinja`_, allowing access to ``{{ config }}``.

    * - .. data:: CONTACT_NAME
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Contact name for inquiries in documentation.

    * - .. data:: CONTACT_EMAIL
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Contact email for inquiries in documentation.

    * - .. data:: CONTACT_URL
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Contact website for inquiries in documentation.

    * - .. data:: LICENCE_NAME
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Licence name for the API.

    * - .. data:: LICENCE_URL
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - URL for the licence.

    * - .. data:: SERVER_URLS
          :bdg:`default:` ``None``
          :bdg:`type` ``list[dict]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - List of server URLs with descriptions for documentation.

    * - .. data:: DOCUMENTATION_HEADERS
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Custom HTML to inject into the documentation ``<head>``. Takes precedence over :data:`DOC_HTML_HEADERS`.

    * - .. data:: DOC_HTML_HEADERS
          :bdg:`default:` ``None``
          :bdg:`type` ``str``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - **Deprecated**. Use :data:`DOCUMENTATION_HEADERS` instead.

    * - .. data:: VERBOSITY_LEVEL
          :bdg:`default:` ``0``
          :bdg:`type` ``int``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Console output verbosity (0–4).

    * - .. data:: ALLOW_NESTED_WRITES
          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Enable POST/PATCH requests to include nested related objects.
    * - .. data:: ENABLE_CORS
          :bdg:`default:` ``False``
          :bdg:`type` ``bool``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Enable Cross-Origin Resource Sharing by calling ``flask_cors.CORS``.
          Resources may be customised via :data:`CORS_RESOURCES`.

    * - .. data:: CORS_RESOURCES
          :bdg:`default:` ``None``
          :bdg:`type` ``dict | list[str]``
          :bdg-secondary:`Optional` :bdg-dark-line:`Global`
        - Resource patterns passed to :func:`flask_cors.CORS`.
          Follows the ``resources`` parameter format from ``flask-cors``.

