[← Back to Advanced Configuration index](index.md)

# Query parameter controls
`flarchitect` can expose several query parameters that let clients tailor
responses. These toggles may be disabled to enforce fixed behaviour.

## Filtering
The API_ALLOW_FILTERS <configuration.html#ALLOW_FILTERS> flag enables a `filter` query parameter for
constraining results. For example:
```
GET /api/books?filter=author_id__eq:1
```

## Ordering
Activate API_ALLOW_ORDER_BY <configuration.html#ALLOW_ORDER_BY> to allow sorting via `order_by`:
```
GET /api/books?order_by=-published_date
```

## Selecting fields
API_ALLOW_SELECT_FIELDS <configuration.html#ALLOW_SELECT_FIELDS> lets clients whitelist response columns with
the `fields` parameter:
```
GET /api/books?fields=title,author_id
```
See configuration <configuration> for detailed descriptions of
API_ALLOW_FILTERS <configuration.html#ALLOW_FILTERS>, API_ALLOW_ORDER_BY <configuration.html#ALLOW_ORDER_BY> and
API_ALLOW_SELECT_FIELDS <configuration.html#ALLOW_SELECT_FIELDS>.

## Joining related resources
Enable API_ALLOW_JOIN <configuration.html#ALLOW_JOIN> to allow clients to join related models using
the `join` query parameter:
```
GET /api/books?join=author&fields=books.title,author.first_name
```

## Grouping and aggregation
API_ALLOW_GROUPBY <configuration.html#ALLOW_GROUPBY> enables the `groupby` parameter for SQL
`GROUP BY` clauses. Use API_ALLOW_AGGREGATION <configuration.html#ALLOW_AGGREGATION> alongside it to
compute aggregates. Aggregates are expressed by appending a label and
function to a field name:
```
GET /api/books?groupby=author_id&id|book_count__count=1
```

