[← Back to Grouping & Aggregation index](index.md)

# Group results
Once `API_ALLOW_GROUPBY` is active, clients can pass a comma-separated
`groupby` query parameter to select columns for the `GROUP BY` clause.
Columns may be referenced by name or fully qualified when joins are
involved:
```
GET /api/books?groupby=author_id
GET /api/invoices?join=customer&groupby=customer.id,customer.currency
```
When grouping is used without aggregates the result set contains the
unique combinations of the requested fields. To return those fields
explicitly, combine `groupby` with `fields=`:
```
GET /api/books?fields=author_id,title&groupby=author_id
```

