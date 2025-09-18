[← Back to Advanced Configuration index](index.md)

# Query parameter controls
`flarchitect` can expose several query parameters that let clients tailor
responses. These toggles may be disabled to enforce fixed behaviour.

## Filtering
Filtering is enabled by default and lets clients constrain results using
`<field>__<operator>=<value>` predicates (e.g. `title__ilike=python`).
Disable it globally or per model with
API_ALLOW_FILTERS <configuration.html#ALLOW_FILTERS>.
See Filtering <filtering> for the complete syntax, supported operators,
OR conditions via `or[ ... ]`, and how to filter on joined models using
`table.column` qualifications.

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
See grouping for more end-to-end examples, supported functions and
response shapes.

