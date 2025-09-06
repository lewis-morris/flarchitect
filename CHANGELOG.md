# CHANGELOG

<!-- version list -->

## Unreleased

### Features

- Performance: request-local caching for configuration/meta lookups.
- Performance: memoization of dynamic schema class creation and subclass lookups.
- Observability: correlation IDs added to every response via `X-Request-ID`.
  - New: optional `request_id` in JSON body via `API_DUMP_REQUEST_ID` (disabled by default).
- Observability: optional structured JSON logging (`API_JSON_LOGS=True`) with request context and latency.
- Docs: spec JSON now served under `/docs/apispec.json` by default; add `API_DOCS_SPEC_ROUTE` to configure the docs JSON path. The top-level `API_SPEC_ROUTE` remains available for `/openapi.json`.

### Bug Fixes

<!-- Replace the placeholders below with concrete entries -->
- TBD: first bug fix summary.
- TBD: second bug fix summary.
- TBD: third bug fix summary.

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
