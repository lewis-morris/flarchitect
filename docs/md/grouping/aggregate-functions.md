[← Back to Grouping & Aggregation index](index.md)

# Aggregate functions
`API_ALLOW_AGGREGATION` unlocks computed values such as totals and
counts. Aggregates are expressed in the query string using the pattern:
```
<column>|<label>__<function>=<placeholder>
```
Where:
- `column` is the base or joined column to aggregate. Qualify the column
    (`table.column`) when grouping across joins.
- `label` is optional. If omitted the API infers `<column>_<function>`.
- `function` is one of `sum`, `count`, `avg`, `min` or `max`.
- `placeholder` can be any value (it is ignored); use `=1` for clarity.
Examples:
```
GET /api/books?groupby=author_id&id|book_count__count=1
GET /api/invoices?join=customer&groupby=customer.id,total|revenue__sum=1
GET /api/payments?amount|avg_amount__avg=1
```
Responses include scalar attributes for each aggregate label alongside any
selected grouping columns:
```
{
  "status_code": 200,
  "value": [
    {"author_id": 1, "book_count": 3},
    {"author_id": 2, "book_count": 5}
  ]
}
```

