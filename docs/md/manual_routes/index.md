# Manual Routes

Before replacing a generated route, see extending_routes: hooks, actions
and operation overrides preserve the generated API while adding business logic.
For a new standalone endpoint, `architect.route` combines registration and the
schema wrapper in one decorator.
flarchitect can wrap your own Flask view functions with the same machinery it
uses for generated endpoints. This is helpful when you hand‑craft a route but
still want consistent authentication, schema validation/serialisation, rate
limiting and OpenAPI documentation.
Use `architect.schema_constructor` to decorate a view and describe how it
should be treated. The decorator applies input/output Marshmallow schemas,
honours auth/roles config, attaches rate limiting, and registers the route for
documentation generation.

## Sections

- [Reserving canonical paths](reserving-canonical-paths.md)
- [Basic usage](basic-usage.md)
- [Input and output schemas](input-and-output-schemas.md)
- [Route handler signature](route-handler-signature.md)
- [Roles and authentication](roles-and-authentication.md)
- [Documentation metadata](documentation-metadata.md)
- [Additional helpers](additional-helpers.md)
