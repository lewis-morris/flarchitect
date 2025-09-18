[← Back to GraphQL index](index.md)

# Type mapping
`create_schema_from_models` converts SQLAlchemy column types into Graphene
scalars using flarchitect.graphql.SQLA_TYPE_MAPPING. Out of the box it
supports `Integer`, `String`, `Boolean`, `Float`, `Date`, `DateTime`,
`Numeric`, `JSON` and `UUID` columns. Custom or proprietary SQLAlchemy
types can be mapped by providing a `type_mapping` override:
```
schema = create_schema_from_models(
    [User], db.session, type_mapping={MyType: graphene.String}
)
```

## Example mutations
`create_schema_from_models` automatically generates `create_<table>`,
`update_<table>` and `delete_<table>` mutations. Each accepts the model's
columns as arguments with the primary key required for updates and deletions.
The examples below create, update and delete an `Item`:
```
mutation {
    create_item(name: "Foo") {
        id
        name
    }
}

mutation {
    update_item(id: 1, name: "Bar") {
        id
        name
    }
}

mutation {
    delete_item(id: 1)
}
```

## Example query
```
query {
    all_items(name: "Foo", limit: 1, offset: 0) {
        id
        name
    }
}
```
Filtering on any column is supported. The following returns all `Item`
objects with `name` equal to `"Bar"`:
```
query {
    all_items(name: "Bar") {
        id
        name
    }
}
```
Visit `/graphql` in a browser to access the interactive GraphiQL editor
served on `GET` requests. Programmatic clients should send HTTP `POST`
requests with a `query` payload.

