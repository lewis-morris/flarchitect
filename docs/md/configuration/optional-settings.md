[← Back to Configuration index](index.md)

# Optional Settings

## Documentation Settings
| Setting | Details |
| --- | --- |
| `DOCUMENTATION_URL_PREFIX`<br>default: `/`<br>type `str`<br>Optional Global | URL prefix for the documentation blueprint. Useful when mounting the app or docs under a subpath (e.g., behind a reverse proxy). Affects both the docs page and its JSON spec route. Example: set to `/api` to serve docs at `/api/docs` and spec at `/api/docs/apispec.json`. |
| `API_CREATE_DOCS`<br>default: `True`<br>type `bool`<br>Optional Global | Controls whether ReDoc documentation is generated automatically. Set to `False` to disable docs in production or when using an external documentation tool. Accepts `True` or `False`. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_DOCUMENTATION_HEADERS`<br>default: ````<br>type `str`<br>Optional Global | Extra HTML placed in the <head> of the docs page. Supply meta tags or script includes as a string or template. |
| `API_DOCUMENTATION_URL`<br>default: `/docs`<br>type `str`<br>Optional Global | URL path where documentation is served. Useful for mounting docs under a custom route such as `/redoc`. Accepts any valid path string. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_DOCUMENTATION_PASSWORD`<br>default: `None`<br>type `str`<br>Optional Global | Protects docs and `apispec.json` with a simple password prompt. Users must enter this password on the docs login screen. |
| `API_DOCUMENTATION_REQUIRE_AUTH`<br>default: `False`<br>type `bool`<br>Optional Global | When `True` the docs login screen accepts user account credentials in addition to the optional password. Requires `API_AUTHENTICATE_METHOD` to be configured. |
| `API_DOCS_STYLE`<br>default: `redoc`<br>type `str`<br>Optional Global | Selects the documentation UI style. Use `redoc` (default) or `swagger` to render with Swagger UI. |
| `API_SPEC_ROUTE`<br>default: `/openapi.json`<br>type `str`<br>Optional Global | Deprecated: now redirects to the docs JSON path. Prefer `API_DOCS_SPEC_ROUTE`. |
| `API_DOCS_SPEC_ROUTE`<br>default: `/docs/apispec.json`<br>type `str`<br>Optional Global | Path of the JSON document used by the documentation UI. Defaults to a doc‑scoped path under `API_DOCUMENTATION_URL`. |
| `API_LOGO_URL`<br>default: `None`<br>type `str`<br>Optional Global | URL or path to an image used as the documentation logo. Useful for branding or product recognition. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_LOGO_BACKGROUND`<br>default: `None`<br>type `str`<br>Optional Global | Sets the background colour behind the logo, allowing alignment with corporate branding. Accepts any CSS colour string. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_FIELD_EXAMPLE_DEFAULTS`<br>default: `{"Integer": 1, "Float": 1.23, "Decimal": 9.99, "Boolean": True}`<br>type `dict`<br>Optional Global | Mapping of Marshmallow field names to example values used when no explicit `example` metadata is provided. |
| `API_DESCRIPTION`<br>type `str or str path`<br>Optional Global | Accepts free text or a filepath to a Jinja template and supplies the description shown on the docs landing page. Useful for providing an overview or dynamically generated content using `{config.xxxx}` placeholders. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_CONTACT_NAME`<br>default: `None`<br>type `str`<br>Optional Global | Human-readable name for API support or maintainer shown in the docs. Leave `None` to omit the contact block. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_CONTACT_EMAIL`<br>default: `None`<br>type `str`<br>Optional Global | Email address displayed for support requests. Use when consumers need a direct channel for help. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_CONTACT_URL`<br>default: `None`<br>type `str`<br>Optional Global | Website or documentation page for further assistance. Set to `None` to hide the link. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_LICENCE_NAME`<br>default: `None`<br>type `str`<br>Optional Global | Name of the licence governing the API, e.g., `MIT` or `Apache-2.0`. Helps consumers understand usage rights. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_LICENCE_URL`<br>default: `None`<br>type `str`<br>Optional Global | URL linking to the full licence text for transparency. Set to `None` to omit. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_SERVER_URLS`<br>default: `None`<br>type `list[dict]`<br>Optional Global | List of server objects defining environments where the API is hosted. Each dict may include `url` and `description` keys. Ideal for multi-environment setups. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_DOC_HTML_HEADERS`<br>default: `None`<br>type `str`<br>Optional Global | HTML `<head>` snippets inserted into the documentation page. Use to add meta tags or analytics scripts. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |

## Routing and Behaviour
| Setting | Details |
| --- | --- |
| `API_PREFIX`<br>default: `/api`<br>type `str`<br>Optional Global | Base path prefix applied to all API routes. Adjust when mounting the API under a subpath such as `/v1`. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_CACHE_TYPE`<br>default: `None`<br>type `str`<br>Optional Global | Flask-Caching backend used for caching `GET` responses. Specify names like `RedisCache` when the `flask-caching` package is installed. Without that dependency, only `SimpleCache` is supported through a small built-in fallback; other values raise a runtime error. |
| `API_CACHE_TIMEOUT`<br>default: `300`<br>type `int`<br>Optional Global | Expiry time in seconds for cached responses. Only applicable when `API_CACHE_TYPE` is set. See api_caching. |
| `API_ENABLE_CORS`<br>default: `False`<br>type `bool`<br>Optional Global | Enables Cross-Origin Resource Sharing. If `flask-cors` is present the settings are delegated to it; otherwise a minimal `Access-Control-Allow-Origin` header is applied based on `CORS_RESOURCES`. |
| `API_ENABLE_WEBSOCKETS`<br>default: `False`<br>type `bool`<br>Optional Global | Enables the optional WebSocket endpoint for real-time event broadcasts. When `True` and the optional dependency `flask_sock` is installed, a WebSocket route is registered (see `API_WEBSOCKET_PATH`). If the dependency is missing, the feature is skipped. |
| `API_WEBSOCKET_PATH`<br>default: `/ws`<br>type `str`<br>Optional Global | URL path exposed by the built-in WebSocket endpoint. Change this to align with your routing scheme, e.g., `/realtime`. |
| `API_XML_AS_TEXT`<br>default: `False`<br>type `bool`<br>Optional Global | When `True`, XML responses are served with `text/xml` instead of `application/xml` for broader client compatibility. |
| `API_VERBOSITY_LEVEL`<br>default: `1`<br>type `int`<br>Optional Global | Verbosity for console output during API generation. `0` silences logs while higher values provide more detail. Example: [tests/test_model_meta/model_meta/config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_model_meta/model_meta/config.py). |
| `API_ENDPOINT_CASE`<br>default: `kebab`<br>type `string`<br>Optional Global | Case style for generated endpoint URLs such as `kebab` or `snake`. Choose to match your project's conventions. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_ENDPOINT_NAMER`<br>default: `endpoint_namer`<br>type `callable`<br>Optional Global | Function that generates endpoint names from models. Override to customise URL naming behaviour. |

## Logging & Observability
| Setting | Details |
| --- | --- |
| `API_JSON_LOGS`<br>default: `False`<br>type `bool`<br>Optional Global | Emit structured JSON logs with request context and latency instead of plain text. Useful for aggregators such as ELK or Loki. |
| `API_LOG_REQUESTS`<br>default: `True`<br>type `bool`<br>Optional Global | Log a single-line summary for each request after it completes. Includes method, path, and status code. |

## Serialisation Settings
| Setting | Details |
| --- | --- |
| `API_FIELD_CASE`<br>default: `snake`<br>type `string`<br>Optional Global | Determines the case used for field names in responses, e.g., `snake` or `camel`. Helps integrate with client expectations. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_SCHEMA_CASE`<br>default: `camel`<br>type `string`<br>Optional Global | Naming convention for generated schemas. Options include `camel` or `snake` depending on tooling preferences. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_PRINT_EXCEPTIONS`<br>default: `True`<br>type `bool`<br>Optional Global | Toggles Flask's exception printing in responses. Disable in production for cleaner error messages. Options: `True` or `False`. |
| `API_BASE_MODEL`<br>default: `None`<br>type `Model`<br>Optional Global | Root SQLAlchemy model used for generating documentation and inferring defaults. Typically the base `db.Model` class. |
| `API_BASE_SCHEMA`<br>default: `AutoSchema`<br>type `Schema`<br>Optional Global | Base schema class used for model serialisation. Override with a custom schema to adjust marshmallow behaviour. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_AUTO_VALIDATE`<br>default: `True`<br>type `bool`<br>Optional Model | Automatically validate incoming data against field types and formats. Disable for maximum performance at the risk of accepting invalid data. |
| `API_GLOBAL_PRE_DESERIALIZE_HOOK`<br>default: `None`<br>type `callable`<br>Optional Global | Callable run on the raw request body before deserialisation. Use it to normalise or sanitise payloads globally. |
| `API_ALLOW_CASCADE_DELETE`<br>default: `False`<br>type `bool`<br>Optional Model | Allows cascading deletes on related models when a parent is removed. Use with caution to avoid accidental data loss. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_IGNORE_UNDERSCORE_ATTRIBUTES`<br>default: `True`<br>type `bool`<br>Optional Model | Ignores attributes prefixed with `_` during serialisation to keep internal fields hidden. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_SERIALIZATION_TYPE`<br>Optional | Output format for serialised data. Options include `url` (default), `json`, `dynamic` and `hybrid`. Determines how responses are rendered. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_SERIALIZATION_DEPTH`<br>Optional | Depth for nested relationship serialisation. `0` (default) keeps relationships as URLs even when `dump=json`/`dump=dynamic`/`dump=hybrid`. Increase to nest that many relationship levels before falling back to URLs. |
| `API_SERIALIZATION_IGNORE_DETACHED`<br>default: `True`<br>type `bool`<br>Optional Global | When enabled, gracefully skips unloaded/detached relationships during dump and returns `None`/`[]` instead of raising `DetachedInstanceError`. Use in combination with `API_SERIALIZATION_DEPTH` to pre-load relations. |
| `API_DUMP_HYBRID_PROPERTIES`<br>default: `True`<br>type `bool`<br>Optional Model | Includes hybrid SQLAlchemy properties in serialised output. Disable to omit computed attributes. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_ADD_RELATIONS`<br>default: `True`<br>type `bool`<br>Optional Model | Adds relationship fields to serialised output, enabling nested data representation. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_PAGINATION_SIZE_DEFAULT`<br>default: `20`<br>type `int`<br>Optional Global | Default number of items returned per page when pagination is enabled. Set lower for lightweight responses. Example: [tests/test_api_filters.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_api_filters.py). |
| `API_PAGINATION_SIZE_MAX`<br>default: `100`<br>type `int`<br>Optional Global | Maximum allowed page size to prevent clients requesting excessive data. Adjust based on performance considerations. |
| `API_READ_ONLY`<br>default: `True`<br>type `bool`<br>Optional Model | When `True`, only read operations are allowed on models, blocking writes for safety. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |

## Query Options
| Setting | Details |
| --- | --- |
| `API_ALLOW_ORDER_BY`<br>default: `True`<br>type `bool`<br>Optional Model | Enables `order_by` query parameter to sort results. Disable to enforce fixed ordering. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_ALLOW_FILTERS`<br>default: `True`<br>type `bool`<br>Optional Model | Allows filtering using query parameters. Useful for building rich search functionality. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_ALLOW_JOIN`<br>default: `False`<br>type `bool`<br>Optional Model | Enables `join` query parameter to include related resources in queries. |
| `API_ALLOW_GROUPBY`<br>default: `False`<br>type `bool`<br>Optional Model | Enables the `groupby` query parameter so queries can add SQL `GROUP BY` clauses. See grouping for examples. |
| `API_ALLOW_AGGREGATION`<br>default: `False`<br>type `bool`<br>Optional Model | Allows aggregate functions like `field|label__sum` or `amount|avg_amount__avg`; pair with `API_ALLOW_GROUPBY`. See grouping for the full syntax. |
| `API_ALLOW_SELECT_FIELDS`<br>default: `True`<br>type `bool`<br>Optional Model | Allows clients to specify which fields to return, reducing payload size. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |

## Method Access Control
| Setting | Details |
| --- | --- |
| `API_ALLOWED_METHODS`<br>default: `[]`<br>type `list[str]`<br>Optional Model | Explicit list of HTTP methods permitted on routes. Only methods in this list are enabled. |
| `API_BLOCK_METHODS`<br>default: `[]`<br>type `list[str]`<br>Optional Model | Methods that should be disabled even if allowed elsewhere, e.g., `["DELETE", "POST"]` for read-only APIs. |

## Authentication Settings
| Column 1 | Column 2 |
| --- | --- |
| `API_AUTHENTICATE`<br>Optional | Enables authentication on all routes. When provided, requests must pass the configured authentication check. Example: [tests/test_authentication.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_authentication.py). |
| `API_AUTHENTICATE_METHOD`<br>Optional | Name of the authentication method used, such as `jwt` or `basic`. Determines which auth backend to apply. Example: [tests/test_authentication.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_authentication.py). |
| `API_ROLE_MAP`<br>default: `None`<br>type `dict | list[str] | str`<br>Optional Global/Model | Config-driven roles for endpoints. Keys may be HTTP methods (`GET`, `POST`, `PATCH`, `DELETE`), `GET_MANY`/`GET_ONE` for GET granularity, `RELATION_GET` for relation routes, or `ALL`/`*` as a fallback. Values can be a list/str of roles (all required) or a dict `{"roles": [..], "any_of": True}`. Example: ``` API_ROLE_MAP = { "GET": ["viewer"], "POST": {"roles": ["editor", "admin"], "any_of": True}, "DELETE": ["admin"], } ``` |
| `API_ROLES_REQUIRED`<br>default: `None`<br>type `list[str]`<br>Optional Global/Model | Simple fallback: list of roles that must all be present on every endpoint for that model. |
| `API_ROLES_ACCEPTED`<br>default: `None`<br>type `list[str]`<br>Optional Global/Model | Simple fallback: list of roles where any grants access on every endpoint for that model. |
| `API_CREDENTIAL_HASH_FIELD`<br>default: `None`<br>type `str`<br>Optional Global | Field on the user model storing a hashed credential for API key auth. Required when using `api_key` authentication. |
| `API_CREDENTIAL_CHECK_METHOD`<br>default: `None`<br>type `str`<br>Optional Global | Name of the method on the user model that validates a plaintext credential, such as `check_password`. |
| `API_KEY_AUTH_AND_RETURN_METHOD`<br>default: `None`<br>type `callable`<br>Optional Global | Custom function for API key auth that receives a key and returns the matching user object. |
| `API_USER_LOOKUP_FIELD`<br>default: `None`<br>type `str`<br>Optional Global | Attribute used to locate a user, e.g., `username` or `email`. |
| `API_CUSTOM_AUTH`<br>default: `None`<br>type `callable`<br>Optional Global | Callable invoked when `API_AUTHENTICATE_METHOD` includes `"custom"`. It must return the authenticated user or `None`. |
| `API_USER_MODEL`<br>Optional<br>- Import path for the user model leveraged during authentication workflows. Example: [tests/test_authentication.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_authentication.py). |  |
| `API_AUTH_ME_ROUTE`<br>default: `/auth/me`<br>type `str`<br>Optional Global | Path for the current-user endpoint that returns the authenticated user as JSON. Applies when a user model is configured and any supported authentication method is enabled (`jwt`, `basic`, `api_key`, or `custom`). Example: set to `/api/auth/me` to expose the endpoint under the API prefix. |
| `API_EXPOSE_ME`<br>default: `True`<br>type `bool`<br>Optional Global | Controls whether the current-user endpoint is registered. Set to `False` to disable it even when a user model is configured. |
| `API_JWT_EXPIRY_TIME`<br>default: `360`<br>type `int`<br>Optional Global | Minutes an access token remains valid before requiring a refresh. |
| `API_JWT_ALGORITHM`<br>default: `HS256`<br>type `str`<br>Optional Global | Algorithm used to sign and verify JWTs. Common choices are `HS256` (HMAC with SHA-256) and `RS256` (RSA with SHA-256). Must match the algorithm used by your tokens. |
| `API_JWT_ALLOWED_ALGORITHMS`<br>default: `None`<br>type `str | list[str]`<br>Optional Global | Allow-list of acceptable algorithms during verification. Accepts a comma-separated string or a Python list. Defaults to the single configured algorithm. |
| `API_JWT_LEEWAY`<br>default: `0`<br>type `int`<br>Optional Global | Number of seconds allowed for clock skew when validating `exp`/`iat`. |
| `API_JWT_ISSUER`<br>default: `None`<br>type `str`<br>Optional Global | Issuer claim to embed and enforce when decoding tokens. |
| `API_JWT_AUDIENCE`<br>default: `None`<br>type `str`<br>Optional Global | Audience claim to embed and enforce when decoding tokens. |
| `API_JWT_REFRESH_EXPIRY_TIME`<br>default: `2880`<br>type `int`<br>Optional Global | Minutes a refresh token stays valid. Defaults to two days (`2880` minutes). |
| `ACCESS_SECRET_KEY`<br>default: `None`<br>type `str`<br>Required for HS* Global | Secret used to sign and verify access tokens for HMAC algorithms (e.g. `HS256`). |
| `REFRESH_SECRET_KEY`<br>default: `None`<br>type `str`<br>Required for HS* Global | Secret used to sign and verify refresh tokens for HMAC algorithms. |
| `ACCESS_PRIVATE_KEY`<br>default: `None`<br>type `str`<br>Required for RS* Global | PEM-encoded private key for signing access tokens when using RSA (e.g. `RS256`). |
| `ACCESS_PUBLIC_KEY`<br>default: `None`<br>type `str`<br>Required for RS* Global | PEM-encoded public key for verifying access tokens when using RSA. |
| `REFRESH_PRIVATE_KEY`<br>default: `None`<br>type `str`<br>Required for RS* Global | PEM-encoded private key for signing refresh tokens when using RSA. |
| `REFRESH_PUBLIC_KEY`<br>default: `None`<br>type `str`<br>Required for RS* Global | PEM-encoded public key for verifying refresh tokens when using RSA. |

## Plugins
| Setting | Details |
| --- | --- |
| `API_PLUGINS`<br>default: `[]`<br>type `list[PluginBase | factory]`<br>Optional Global | Register plugins to observe or modify behaviour via stable hooks (request lifecycle, model ops, spec build). Entries may be PluginBase subclasses, instances, or factories returning a PluginBase. Invalid entries are ignored. |

## Callback Hooks
| Setting | Details |
| --- | --- |
| `API_GLOBAL_SETUP_CALLBACK`<br>default: `None`<br>type `callable`<br>Optional Global | Runs before any model-specific processing. |
| `API_FILTER_CALLBACK`<br>default: `None`<br>type `callable`<br>Optional Model | Adjusts the SQLAlchemy query before filters or pagination are applied. |
| `API_ADD_CALLBACK`<br>default: `None`<br>type `callable`<br>Optional Model | Invoked prior to committing a new object to the database. |
| `API_UPDATE_CALLBACK`<br>default: `None`<br>type `callable`<br>Optional Model | Called before persisting changes to an existing object. |
| `API_REMOVE_CALLBACK`<br>default: `None`<br>type `callable`<br>Optional Model | Executed before deleting an object from the database. |
| `API_SETUP_CALLBACK`<br>default: `None`<br>type `callable`<br>Optional Model Method | Function executed before processing a request, ideal for setup tasks or validation. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_RETURN_CALLBACK`<br>default: `None`<br>type `callable`<br>Optional Model Method | Callback invoked to modify the response payload before returning it to the client. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_ERROR_CALLBACK`<br>default: `None`<br>type `callable`<br>Optional Global | Error-handling hook allowing custom formatting or logging of exceptions. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_DUMP_CALLBACK`<br>default: `None`<br>type `callable`<br>Optional Model Method | Post-serialisation hook to adjust data after Marshmallow dumping. |
| `API_FINAL_CALLBACK`<br>default: `None`<br>type `callable`<br>Optional Global | Executes just before the response is serialised and returned to the client. |
| `API_ADDITIONAL_QUERY_PARAMS`<br>default: `None`<br>type `list[dict]`<br>Optional Model Method | Extra query parameters supported by the endpoint. Each dict may contain `name` and `schema` keys. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |

## Response Metadata
| Setting | Details |
| --- | --- |
| `API_DUMP_DATETIME`<br>default: `True`<br>type `bool`<br>Optional Global | Appends the current UTC timestamp to responses for auditing. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_DUMP_VERSION`<br>default: `True`<br>type `bool`<br>Optional Global | Includes the API version string in every payload. Helpful for client-side caching. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_DUMP_STATUS_CODE`<br>default: `True`<br>type `bool`<br>Optional Global | Adds the HTTP status code to the serialised output, clarifying request outcomes. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_DUMP_RESPONSE_MS`<br>default: `True`<br>type `bool`<br>Optional Global | Adds the elapsed request processing time in milliseconds to each response. |
| `API_DUMP_TOTAL_COUNT`<br>default: `True`<br>type `bool`<br>Optional Global | Includes the total number of available records in list responses, aiding pagination UX. |
| `API_DUMP_REQUEST_ID`<br>default: `False`<br>type `bool`<br>Optional Global | Includes the per-request correlation ID in the JSON response body. The header `X-Request-ID` is always present. |
| `API_DUMP_NULL_NEXT_URL`<br>default: `True`<br>type `bool`<br>Optional Global | When pagination reaches the end, returns `null` for `next` URLs instead of omitting the key. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_DUMP_NULL_PREVIOUS_URL`<br>default: `True`<br>type `bool`<br>Optional Global | Ensures `previous` URLs are present even when no prior page exists by returning `null`. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_DUMP_NULL_ERRORS`<br>default: `True`<br>type `bool`<br>Optional Global | Ensures an `errors` key is always present in responses, defaulting to `null` when no errors occurred. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |

## Rate Limiting and Sessions
| Setting | Details |
| --- | --- |
| `API_RATE_LIMIT`<br>default: `None`<br>type `str`<br>Optional Model Method | Rate limit string using Flask-Limiter syntax (e.g., `100/minute`) to throttle requests. Example: [tests/test_flask_config.py](https://github.com/lewis-morris/flarchitect/blob/master/tests/test_flask_config.py). |
| `API_RATE_LIMIT_STORAGE_URI`<br>default: `None`<br>type `str`<br>Optional Global | URI for the rate limiter's storage backend, e.g., `redis://127.0.0.1:6379`. When omitted, `flarchitect` probes for Redis, Memcached, or MongoDB and falls back to in-memory storage. Use this to pin rate limiting to a specific service instead of auto-detection. |
| `API_RATE_LIMIT_AUTODETECT`<br>default: `True`<br>type `bool`<br>Optional Global | Controls automatic detection of local rate limit backends (Redis/Memcached/MongoDB). Set to `False` to disable probing in restricted environments. |
| `API_SESSION_GETTER`<br>default: `None`<br>type `callable`<br>Optional Global | Callable returning a SQLAlchemy ~sqlalchemy.orm.Session. Provides manual control over session retrieval when automatic resolution is insufficient, such as with custom session factories or multiple database binds. If unset, `flarchitect` attempts to locate the session via Flask-SQLAlchemy, model `query` attributes, or engine bindings. |

## Field Inclusion Controls
| Setting | Details |
| --- | --- |
| `IGNORE_FIELDS`<br>default: `None`<br>type `list[str]`<br>Optional Model Method | Intended list of attributes hidden from both requests and responses. Use it when a column should never be accepted or exposed, such as `internal_notes`. At present the core does not process this flag, so filtering must be handled manually. |
| `IGNORE_OUTPUT_FIELDS`<br>default: `None`<br>type `list[str]`<br>Optional Model Method | Fields accepted during writes but stripped from serialised responses—ideal for secrets like `password`. This option is not yet wired into the serialiser; custom schema logic is required to enforce it. |
| `IGNORE_INPUT_FIELDS`<br>default: `None`<br>type `list[str]`<br>Optional Model Method | Attributes the API ignores if clients supply them, while still returning the values when present on the model. Useful for server-managed columns such as `created_at`. Currently this flag is informational and does not trigger automatic filtering. |

## Soft Delete
| Setting | Details |
| --- | --- |
| `API_SOFT_DELETE`<br>default: `False`<br>type `bool`<br>Optional Global | Marks records as deleted rather than removing them from the database. See soft-delete. When enabled, `DELETE` swaps a configured attribute to its "deleted" value unless `?cascade_delete=1` is sent. Example: ``` class Config: API_SOFT_DELETE = True ``` |
| `API_SOFT_DELETE_ATTRIBUTE`<br>default: `None`<br>type `str`<br>Optional Global | Model column that stores the delete state, such as `status` or `is_deleted`. `flarchitect` updates this attribute to the "deleted" value during soft deletes. Example: ``` API_SOFT_DELETE_ATTRIBUTE = "status" ``` |
| `API_SOFT_DELETE_VALUES`<br>default: `None`<br>type `tuple`<br>Optional Global | Two-element tuple defining the active and deleted markers for `API_SOFT_DELETE_ATTRIBUTE`. For example, `("active", "deleted")` or `(1, 0)`. The second value is written when a soft delete occurs. |
| `API_ALLOW_DELETE_RELATED`<br>default: `True`<br>type `bool`<br>Optional Model Method | Historical flag intended to control whether child records are deleted alongside their parent. The current deletion engine only honours `API_ALLOW_CASCADE_DELETE`, so this setting is ignored. Leave it unset unless future versions reintroduce granular control. |
| `API_ALLOW_DELETE_DEPENDENTS`<br>default: `True`<br>type `bool`<br>Optional Model Method | Companion flag to `API_ALLOW_DELETE_RELATED` covering association-table entries and similar dependents. Not currently evaluated by the code base; cascade behaviour hinges solely on `API_ALLOW_CASCADE_DELETE`. Documented for completeness and potential future use. |

## Endpoint Summaries
| Setting | Details |
| --- | --- |
| `GET_MANY_SUMMARY`<br>default: `None`<br>type `str`<br>Optional Model Method | Customises the `summary` line for list endpoints in the generated OpenAPI spec. Example: `get_many_summary = "List all books"` produces that phrase on `GET /books`. Useful for clarifying collection responses at a glance. |
| `GET_SINGLE_SUMMARY`<br>default: `None`<br>type `str`<br>Optional Model Method | Defines the doc summary for single-item `GET` requests. `get_single_summary = "Fetch one book by ID"` would appear beside `GET /books/{id}`. Helps consumers quickly grasp endpoint intent. |
| `POST_SUMMARY`<br>default: `None`<br>type `str`<br>Optional Model Method | Short line describing the create operation in documentation. For instance, `post_summary = "Create a new book"` labels `POST /books` accordingly. Particularly handy when auto-generated names need clearer wording. |
| `PATCH_SUMMARY`<br>default: `None`<br>type `str`<br>Optional Model Method | Sets the summary for `PATCH` endpoints used in the OpenAPI docs. Example: `patch_summary = "Update selected fields of a book"`. Provides readers with a concise explanation of partial updates. |

