[← Back to SQLAlchemy Models index](index.md)

# Nested relationship dumping
API_ADD_RELATIONS <configuration.html#ADD_RELATIONS> controls whether relationship fields are included in the
serialised response. Disable it to return only column data, or use
`?dump_relationships=false` on a request to temporarily suppress all
relationships.
API_SERIALIZATION_DEPTH <configuration.html#SERIALIZATION_DEPTH> limits how many levels of related resources are
embedded. `0` (default) keeps them as URLs even with `dump=json` or
`dump=dynamic`. Increase the depth to inline that many relationship levels
before falling back to URLs.
For API_SERIALIZATION_TYPE <configuration.html#SERIALIZATION_TYPE> set to `"dynamic"`, clients can choose which
relationships to embed by supplying a comma-separated `join` parameter, e.g.
`?join=books,publisher`. Any relationships not listed are returned as URLs.

## Example responses
URL-only dump (depth `1`):
```
GET /api/authors/1
{
    "id": 1,
    "name": "Alice",
    "books": "/api/authors/1/books"
}
```
JSON dump (depth `1`):
```
GET /api/authors/1?dump=json
{
    "id": 1,
    "name": "Alice",
    "books": [
        {"id": 10, "title": "Example", "publisher": "/api/publishers/5"}
    ]
}
```
JSON dump (depth `2` with API_SERIALIZATION_DEPTH <configuration.html#SERIALIZATION_DEPTH> = `2` or `?join=books,publisher`):
```
GET /api/authors/1?dump=json
{
    "id": 1,
    "name": "Alice",
    "books": [
        {"id": 10, "title": "Example", "publisher": {"id": 5, "name": "ACME"}}
    ]
}
```
Hybrid dump:
```
GET /api/authors/1?dump=hybrid
{
    "id": 1,
    "name": "Alice",
    "books": "/api/authors/1/books",
    "publisher": {"id": 5, "name": "ACME"}
}
```

