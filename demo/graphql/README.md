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

Additional examples, including a small Python client, live alongside this file.
