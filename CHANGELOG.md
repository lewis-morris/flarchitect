# CHANGELOG

<!-- version list -->

## Unreleased

- Auth: Auto-register `POST` refresh route when JWT is enabled, with configurable path and idempotent registration
  - New config: `API_AUTO_AUTH_ROUTES` (default `True`) to disable built-in auth endpoints.
  - New config: `API_AUTH_REFRESH_ROUTE` (default `/auth/refresh`) to change the refresh path.
  - Behaviour unchanged by default; uses existing response wrapper and token rotation.

- Improve 403 role errors with required roles + context
  - Added helpers to normalise/resolve role specs from `API_ROLE_MAP`.
  - Enriched 403 responses on role mismatch with: `required_roles`, `any_of`, `method`, `path`, `resource`, best‑effort `user` and `lookup`, `resolved_from`, and `reason`.
  - Preserves existing behaviour for success paths and when configuration/helpers are absent.

### Features

- Performance: request-local caching for configuration/meta lookups.
- Performance: memoization of dynamic schema class creation and subclass lookups.
- Observability: correlation IDs added to every response via `X-Request-ID`.
  - New: optional `request_id` in JSON body via `API_DUMP_REQUEST_ID` (disabled by default).
- Observability: optional structured JSON logging (`API_JSON_LOGS=True`) with request context and latency.
- Docs: spec JSON now served under `/docs/apispec.json` by default; add `API_DOCS_SPEC_ROUTE` to configure the docs JSON path. The top-level `API_SPEC_ROUTE` remains available for `/openapi.json`.
- Routing: Configurable relation route naming via `API_RELATION_ROUTE_NAMING` and `Meta.relation_route_naming` ("model" | "relationship" | "auto"). Default remains "model" for compatibility. "auto" switches to relationship key naming only when it avoids collisions. Optional `Meta.relation_route_map` allows aliasing relationship keys in URLs when relationship‑based naming is used.

### Bug Fixes

- Serialization: Prevent DetachedInstanceError by eager-loading relations when `API_ADD_RELATIONS=true` and `API_SERIALIZATION_DEPTH>0`; add detached-safe attribute access.
  - New: `API_SERIALIZATION_IGNORE_DETACHED` (default `True`) to gracefully skip unloaded relations during dump.
  - Relation URL helpers now return safe defaults (`None`/`[]`) when objects are detached.

- Routing: `to_url` now uses SQLAlchemy `Column.key` (mapped attribute name) rather than `Column.name` (DB column) when resolving primary key attributes, fixing AttributeError for models with renamed DB columns.

- Decorators: Allow `output_schema=None` to bypass Marshmallow serialisation and return the raw handler output wrapped in the standard response envelope. Also filter wrapper kwargs to only those accepted by the handler's function signature to avoid `TypeError` from unexpected keywords (e.g. `model`).

### Documentation

- Configuration: Add missing `DOCUMENTATION_URL_PREFIX` to the configuration reference; clarify default and example usage.
- Docs: Clarify that models require a `Meta` inner class for auto-registration, while `tag` and `tag_group` are optional; warnings added in Quick Start, Models guide, and README.
- Docs: Expanded callbacks & plugins guide with full lifecycle, signatures, context keys and practical examples.

## v1.1.0 (2025-08-14)

### Bug Fixes

- **specs**: Register tags for OpenAPI docs
  ([`3851c00`](https://github.com/lewis-morris/flarchitect/commit/3851c002e95f5a55c916f59d16cfa3a72b329e71))

### Chores

- **ci**: Consolidate docs workflows
  ([`358558c`](https://github.com/lewis-morris/flarchitect/commit/358558c0dcab041fed6c0965487328f049740a86))

### Documentation

- **auth**: Document role setup and link guides
  ([`91eb9cf`](https://github.com/lewis-morris/flarchitect/commit/91eb9cf36c0f5087c67249e627aa7f150a3d8429))

### Features

- **authentication**: Add roles_accepted decorator
  ([`ebbf077`](https://github.com/lewis-morris/flarchitect/commit/ebbf077aadf7aff174a859465de4825436d88d61))


## v1.0.0 (2025-08-14)

- Initial Release

## v0.1.2 (2024-03-05)

- Total rework of the configuration system allowing fine-grained control over the application.
- Automated tests added.
- Rate-limiting option added to the configuration.
- Refactoring and more.

## v0.1.1 (2024-02-05)

- Project structure reorganised.
- README.md updated; work on documentation has begun.
- Changes to the config.

## v0.1.0 (2024-01-01)

- Initial project created.
- Minimal working example.
### Testing & Quality

- Increase unit test coverage above 90% with additional tests for responses serialisation, logging, core utilities, WebSocket event bus, and schema models. Mark the optional `init_websockets` endpoint as excluded from coverage as it requires `flask_sock` at runtime.
