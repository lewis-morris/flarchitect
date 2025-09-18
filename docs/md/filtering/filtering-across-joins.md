[← Back to Filtering index](index.md)

# Filtering across joins
When you join related models, you can qualify a filter with the table name using
`table.column__operator=value`. Combine this with `join` to constrain by a
related model’s columns.
```

# Join customers and filter by customer name (case‑insensitive)
GET /api/invoices?join=customer&customer.name__ilike=acme


# Multiple filters still combine with AND
GET /api/invoices?join=customer&customer.name__ilike=acme&total__ge=100
```

