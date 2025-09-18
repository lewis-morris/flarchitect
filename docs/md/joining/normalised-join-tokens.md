[← Back to Joining Related Resources index](index.md)

# Normalised join tokens
The `join` query parameter accepts a comma‑separated list of relationship
names. Each token is normalised so that clients have flexibility when naming
relations:
- Case‑insensitive; leading/trailing whitespace is ignored.
- Hyphens are treated as underscores (`invoice-lines` → `invoice_lines`).
- Matches any of the following for each relationship:
    - the endpoint name (pluralised, using `API_ENDPOINT_CASE`),
    - the relationship key in endpoint case (often singular),
    - the raw SQLAlchemy relationship key.
- Singular/plural variants are resolved automatically.
Examples:
```

# join using endpoint names (plural)
GET /api/books?join=authors


# join using relationship keys (snake case)
GET /api/books?join=author


# multiple joins, any separator: kebab, snake, singular/plural
GET /api/invoices?join=invoice-lines,payment,payments,customer,customers
```

