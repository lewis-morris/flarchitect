# GraphQL

flarchitect can expose SQLAlchemy models through a GraphQL API. The
flarchitect.graphql.create_schema_from_models helper builds a Graphene
schema from your models, while flarchitect.Architect.init_graphql
registers a `/graphql` endpoint and documents it in the OpenAPI spec.

## Sections

- [Quick start](quick-start.md)
- [Type mapping](type-mapping.md)
- [Advanced usage](advanced-usage.md)
- [Tips and trade-offs](tips-and-trade-offs.md)
