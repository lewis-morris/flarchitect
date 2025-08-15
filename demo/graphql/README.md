# GraphQL Demo

This example shows how to expose SQLAlchemy models via GraphQL using `flarchitect`. It spins up a tiny in-memory database and serves a `/graphql` endpoint.

## Running the demo

```bash
python demo/graphql/load.py
```

Open `http://localhost:5000/graphql` in your browser to explore the schema with GraphiQL. You can also send queries from the command line using `curl` or `requests`.

## Sample queries

Fetch all items via the `all_items` query:

```graphql
query {
    all_items {
        id
        name
    }
}
```

Create a new item with the `create_item` mutation:

```graphql
mutation {
    create_item(name: "Biscuit") {
        id
        name
    }
}
```

Filter and paginate results:

```graphql
query {
    all_items(name: "Biscuit", limit: 5, offset: 0) {
        id
        name
    }
}
```

Update and delete items:

```graphql
mutation {
    update_item(id: 1, name: "Cookie") { id name }
    delete_item(id: 1)
}
```

Relationship queries:

```graphql
query {
    all_items {
        id
        name
        category { id name }
    }
}
```

Additional examples, including a small Python client and an advanced schema
showcasing relationships and pagination, live alongside this file.
