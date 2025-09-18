[← Back to GraphQL index](index.md)

# Quick start
The simplest way to enable GraphQL is to feed your models to
`create_schema_from_models` and register the resulting schema with the
architect:
```
schema = create_schema_from_models([User], db.session)
architect.init_graphql(schema=schema)
```
The generated schema provides CRUD-style queries and mutations for each model.
An `all_items` query returns every `Item` and accepts optional column
arguments for filtering. Pagination is supported via `limit` and
`offset` arguments. `create_item`, `update_item` and `delete_item`
mutations manage individual records.

