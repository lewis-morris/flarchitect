## Security

 - [ ] S063 - Secret Management : Centralise secrets via env vars and optional file-based secrets; validate at startup and redact in logs.

 - [ ] S064 - JWKS & Key Rotation : Support JWKS URL retrieval/caching with `kid`-based key selection to enable seamless rotation.

## Developer Experience

 - [ ] S065 - CLI Scaffolding : Add `flarchitect` CLI (init app, generate demo model, manage config, print OpenAPI).

 - [ ] S066 - Pre-commit Quality Gates : ruff + mypy (strict), bandit/safety, coverage thresholds, and CodeQL; ship pre-commit config.

 - [ ] S098 - MCP Client Guides : Publish configuration examples for popular MCP clients/agents and scripts for quick local connection tests.

 - [ ] S103 - CLI Shebang Normalisation : Ensure generated entrypoints resolve the active virtualenv path so relocations (e.g. different mount roots) keep CLI tooling usable without manual rewrites.

 - [ ] S105 - MCP Tool Quickstart : Document sample MCP CLI invocations (search_docs/get_doc_section) and the expected `structuredContent` payloads for faster smoke testing.

 - [ ] S128 - Frontend SDK : Build a TypeScript client that wraps flarchitect REST/GraphQL features with query builders, auth helpers, realtime updates, and typed envelopes; ship tests, examples, and docs.


- [ ] S138 - App-less Schema Config : Allow AutoSchema to use sensible defaults without requiring a Flask app context so unit tests and CLI scripts can generate schemas without manual context scaffolding.

 - [ ] S141 - Response Case Strategy Hooks : Add configuration and docs for supplying custom casing functions to response utilities so teams can enforce project-specific naming schemes.

 - [ ] S145 - Schema Discovery CLI : Ship a CLI command that calls `schema/discovery`, pretty-prints model metadata, and supports depth/model filters for local debugging.

## Architecture & Extensibility

 - [ ] S080 - Plugin Examples Gallery : Curated examples of common plugins (audit, metrics, multi-tenancy) with code and tests.

 - [ ] S068 - Signals/Event Bus : Emit CRUD signals (e.g., with blinker) for decoupled listeners and extensions.

## API & Spec

 - [ ] S069 - Deterministic Spec : Stable operationIds and deterministic ordering; collision guards for re-registration.

 - [ ] S070 - Schema Filters & Metadata : Per-field include/exclude, examples and deprecation markers; override descriptions.

 - [ ] S088 - Route Naming Strategy : Add flexible relation-route naming strategy (model|relationship|auto) with per-model overrides and alias map; ensure deterministic operationIds.

 - [ ] S110 - Join Pagination Docs & Semantics : Document that `join` paginates over distinct base entities; clarify `total_count` behavior and add examples for one-to-many joins.

 - [ ] S121 - OpenAPI: OR & Qualified Filters : Advertise `or[...]` support and `table.column__op=value` filtering in the generated spec so interactive docs reflect real query capabilities; include examples.

 - [ ] S139 - Converter Metadata : Extend parameter schema generation to cover UUID, float, and custom converters with documented defaults so OpenAPI signatures stay precise across routing setups.

## Performance

 - [ ] S071 - Conditional Requests : ETag/Last-Modified support with If-None-Match/If-Modified-Since handling.

 - [ ] S072 - Cache Controls : Configurable `Cache-Control` headers and microcaching for generated spec responses.

## Features

 - [ ] S073 - Bulk Operations : Batch create/update/delete with transactional semantics and partial failure reporting.

 - [ ] S074 - Webhooks : Outbound webhook subscriptions on CRUD events with retries and HMAC signing.

 - [ ] S089 - Relationship Aliases : Expose per-relationship aliasing via `Meta.relation_route_map` with validation and documentation examples.

 - [ ] S113 - Right Join Semantics : Investigate safe support for RIGHT JOIN across dialects and document limitations; consider reversing join order when feasible.

## Testing & Quality

 - [ ] S075 - Property-Based Tests : Hypothesis-driven CRUD roundtrip tests across generated models.

 - [ ] S076 - Performance Benchmarks : Baseline latency/throughput tests for core endpoints and budgets.

 - [ ] S082 - WS Endpoint Tests : Add integration tests for optional WebSocket endpoint behind `flask_sock` when dependency is available.

 - [ ] S099 - Response Envelope Fuzz Tests : Use property-based strategies to exercise `create_response` and `handle_result` across tuple, dict, and CustomResponse-like inputs to harden the serialization contract.

 - [ ] S100 - FastMCP Integration Suite : Stand up an automated integration test hitting a real `fastmcp` runtime to detect API shifts before release.

 - [ ] S144 - Error Callback Contract Tests : Add regression tests ensuring custom error callbacks receive normalised payloads for HTTP exceptions and manual responses.

## Documentation

 - [ ] S077 - Security Hardening Guide : Deployment checklist (secrets, algorithms, CORS, cookies) and incident response notes.

 - [ ] S079 - RBAC & ABAC Guide : Role- and attribute-based access control patterns with examples and best practices.

 - [ ] S093 - Plugin Cookbook : Real-world plugin patterns (audit, multi-tenant scoping, outbox events) building on new lifecycle docs.

 - [ ] S117 - Docs Cross‑Links & Examples : Add cross‑links between joining, filtering, sorting and custom serialisation with concise curl examples on each page.

 - [ ] S114 - Query Params: dump & join_type : Expand README and docs with per-request `dump` override and `join_type` values with examples for dynamic/json/url/hybrid.

 - [ ] S129 - Aggregation Docs : Document labelled aggregation query patterns and surface response examples matching the `<column>|<label>__<function>` format.

 - [ ] S143 - Access Policy Cookbook : Expand documentation with end-to-end access policy examples (owner-only, tenant scoping, soft deletes) and recommended testing strategies for custom policies.

## Complete

 - [x] S146 - Auth Token Providers : Added configurable token extractor pipeline (header, cookie, custom callables) shared by auto routes and `jwt_authentication`, plus helper exports and regression tests.

 - [x] S147 - Cookie Utilities : Introduced `load_user_from_cookie` and `cookie_settings()` so blueprints can reuse hardened cookie policies; documented usage and shipped unit tests.

 - [x] S148 - Schema Discovery Endpoint : Implemented `GET /schema/discovery` with model filtering, depth controls, OpenAPI wiring, and coverage to surface operators/joins at runtime.

 - [x] S149 - Docs Bundle Endpoint : Added `GET /docs/bundle` to merge auto-generated and manual routes with conflict detection and guard rails; included docs and tests.

 - [x] S150 - SSE Helper Suite : Exposed schema-aware SSE helpers (`sse_message`, `stream_model_events`) for typed EventSource payloads alongside comprehensive documentation and tests.

 - [x] S151 - Docs Login User Binding : Updated documentation login to authenticate against the configured user model when required, reusing credential check helpers and refreshing the guides.

 - [x] S142 - JWT Payload Integer Coercion : Align `get_user_from_token` with access token generation by asserting required claims and coercing integer-backed payload fields to ints before querying so PostgreSQL comparisons no longer fail on type mismatches.

 - [x] S127 - Serialization Error Handling : Flatten Marshmallow dump/load validation errors into field-specific envelopes so serialization failures always return structured API responses.

 - [x] S130 - Invoice Aggregates : Normalise join tokens before building the column map and unwrap hybrid properties to their SQL expressions when aggregating so invoice queries handle `payments` joins and `total_outstanding` sums without driver errors.

 - [x] S124 - Bugfix : Forward decorator kwargs to auto routes so POST/PATCH payloads reach CRUD services; regression covered by tests.

 - [x] S104 - MCP Result Envelope : Align docs MCP tool outputs with MCP result schema to fix client validation errors and add regression coverage.

 - [x] S013 - JWT Hardening : Leeway, aud/iss, allowed algorithms, RS256 key pairs supported and documented.

 - [x] S014 - Token Rotation : Implemented refresh token rotation (single-use), revocation (deny-list), and last-used auditing with tests and docs.

 - [x] S078 - Auth Cookbook : JWT, Basic and API key patterns; role mapping examples; multi-tenant considerations.

 - [x] S067 - Plugin Hooks : Formal pre/post hooks for request lifecycle, model ops, and schema build with stable signatures.

 - [x] S081 - Coverage Budget : Raise coverage above 90% by adding focused tests for responses, logging, core utils, websockets bus, and schema models. Excluded optional `init_websockets` from coverage accounting.

 - [x] S083 - Docs Spec Route : Serve docs JSON at `/docs/apispec.json` and add `API_DOCS_SPEC_ROUTE` setting; updated tests and documentation accordingly.

 - [x] S084 - Config Docs: Document `DOCUMENTATION_URL_PREFIX` default and usage in the configuration reference; ensures discoverability of the docs prefix setting.

 - [x] S085 - Meta Requirement Docs : Make it explicit that models without a `Meta` inner class are not auto-registered for routes or documentation; add warnings to README and docs.

 - [x] S086 - Optional Tag Grouping : Document that `Meta.tag` and `Meta.tag_group` are optional; ensure generator defaults to a safe tag when absent.

 - [x] S087 - Relation Key Endpoints : Use relation attribute key in relation routes and endpoint names to avoid collisions when multiple FKs target the same model; initial compatibility via config, later superseded by `API_RELATION_ROUTE_NAMING` with richer controls; docs/tests updated.

 - [x] S090 - 403 Role Error Enrichment : Enrich 403 responses on role mismatch with required roles, matching semantics, request context, resolved config key, and best‑effort user/lookup info; driven by `API_ROLE_MAP`.

 - [x] S091 - Auto Auth Refresh Route : Auto-register POST `/auth/refresh` when JWT is enabled; configurable via `API_AUTO_AUTH_ROUTES` and `API_AUTH_REFRESH_ROUTE`; idempotent registration; tests and docs added.

- [x] S092 - Callback & Plugin Docs : Comprehensive lifecycle, signatures, expected kwargs and examples for callbacks and the plugin system.

- [x] S094 - Serialization Resilience : Eager-load first/nested relations per `API_SERIALIZATION_DEPTH` to avoid lazy-loads during dump; add `API_SERIALIZATION_IGNORE_DETACHED` to return safe defaults for unloaded relations and prevent `DetachedInstanceError`.

- [x] S095 - to_url Uses Column.key : Fix to prefer SQLAlchemy Column.key (mapped attribute name) over Column.name when building URLs, supporting models with renamed DB columns.

- [x] S120 - Filtering Docs : Add a dedicated Filtering guide covering enable/disable via `API_ALLOW_FILTERS`, operator syntax, AND/OR logic with `or[...]`, and joined-table filters using `table.column__op=value`; wire into ToC and cross-link from Advanced Configuration. Ensure `convert_docs.py` generates Markdown.

- [x] S133 - Dynamic Join Depth Override : Ensure default `dump=dynamic` configurations honour explicit join tokens even when `API_SERIALIZATION_DEPTH=0`, so requested relationships inline nested payloads with `API_ADD_RELATIONS=False`; regression test added.

- [x] S134 - Serialization Depth Zero Handling : Preserve URL-only relationship dumps when `API_SERIALIZATION_DEPTH=0` and `dump=json`, restoring expected behaviour alongside the dynamic join override.

- [x] S123 - Dynamic Join Regression : Add tests ensuring `dump=dynamic` inlines requested relations when `API_ADD_RELATIONS=False`, covering comma-separated, repeated `join` params, and additional-key tokens.

- [x] S096 - Optional Output Schema & Kwarg Filtering : Support `output_schema=None` to pass raw handler output through unchanged and filter wrapper kwargs to the handler signature to prevent unexpected keyword errors.

 - [x] S097 - MCP Docs Server : Added `DocumentIndex`, optional `flarchitect-mcp-docs` MCP server with `fastmcp`/reference backends, CLI wiring, tests, and documentation so agents can browse project docs.

 - [x] S101 - FastMCP Backend Compatibility : Update docs server wiring to use the modern `fastmcp` resource/tool APIs, restoring the fast backend for MCP docs browsing.

 - [x] S102 - FastMCP ToolResult Fallback : Handle `fastmcp` 2.12 module layout and loosen tool annotations so docs tooling keeps working across upstream releases.

 - [x] S106 - MCP 2025 Spec Compliance : Update the docs MCP server to advertise 2025-06-18 capabilities, use slash-delimited verbs, camelCase payloads, and structured tool outputs with regression tests and docs.

 - [x] S111 - Join Param Consistency Docs : Clarify that `join` accepts relationship keys (e.g., `author`) or endpoint-style plural names (e.g., `authors`) and is comma-separated; include examples for dynamic/json/url dump types. Also document repeated `join` parameters and additional keys as join tokens.

 - [x] S119 - Join Parser Improvements : Preserve repeated `join` parameters, accept additional keys matching relationship names as join tokens, normalise tokens (case, hyphen→underscore), try singular/plural variants, and return `400 Invalid join model: <token>` on failure; update docs and tests.

 - [x] S107 - MCP Docs Fallback : Default the docs index to Sphinx sources, convert RST to plain text, and fall back to the packaged docs when the project tree lacks `docs/source` so the CLI keeps working in embedded installs.

 - [x] S108 - Markdown Docs Export : Generate semantic Markdown chunks, publish `llms.txt`, ship the conversion script, and update the MCP index/tests to serve the Markdown-first docs set.

 - [x] S109 - Join Pagination Correctness : Apply DISTINCT on base entity when joining without select/group/aggregation so `limit` and `total_count` reflect base rows rather than multiplied join rows; add regression test.

 - [x] S112 - Multi-Join Dynamic Dump : Normalise `join` handling to accept relationship keys or endpoint-style plural names and support comma-separated multi-joins in dynamic serialization; add regression tests.

 - [x] S115 - Join Token Normalisation in Query : Normalise `join` tokens in query building (case-insensitive, hyphen-to-underscore, singular/plural) and resolve via relationship keys and endpoint names; add tests.

 - [x] S116 - Per-request Dump & join_type : Add `dump` query param to override serialization type per request and `join_type` to choose inner/left/right/outer joins; retain pagination distinct fix; add tests and docs.
 
 - [x] S118 - Docs Restructure for LLMs : Split `advanced_configuration.rst` into themed pages (joining, custom_serialization, rate_limiting, caching, response_metadata), add Feature Overview, Troubleshooting, update toctrees, regenerate Markdown and `llms.txt`.

 - [x] S122 - Auth Me Endpoint : Provide `GET /auth/me` returning the current authenticated user (when a user model is configured); documented under Authentication.

 - [x] S122 - Join + Serialization Interop : Allow explicit joins to include related fields even when `API_ADD_RELATIONS=false` by honoring `dump=dynamic&join=...`; add dictionary fallback for `fields` spanning joined tables so selected columns are preserved; update docs and add regression tests.

 - [x] S126 - Grouping Docs : Document enabling `API_ALLOW_GROUPBY`/`API_ALLOW_AGGREGATION`, add a dedicated grouping guide with query examples, cross-link configuration tables, and note the OpenAPI cards.

 - [x] S125 - Serialization Depth Defaults : Treat unset `API_SERIALIZATION_DEPTH` as unlimited and keep `API_SERIALIZATION_TYPE=False` behaving like JSON so hybrid/json tests pass.

- [x] S135 - DB Utils Fallbacks : Allow database operations imports to succeed when `flarchitect.database.utils` is monkeypatched with lightweight stubs by providing safe defaults for normalising join tokens and deriving table names so recursive delete tests can run.

- [x] S137 - Decorator Test Coverage : Added tests for `add_dict_to_query` single-row conversion, pagination previous-link handling, and `fields` schema-instance filtering to harden decorator edge cases.

- [x] S136 - Hybrid Type Hint Evaluation : Resolve string-return annotations on hybrid properties via `typing.get_type_hints` so AutoSchema selects numeric Marshmallow fields and keeps response types aligned when annotations are postponed.

- [x] S140 - Response Case Conversion Fix : Hardened response metadata utilities to respect callable case transformers so camel-case envelopes stay consistent across configuration modes.
