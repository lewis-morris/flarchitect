[← Back to Filtering index](index.md)

# Basic syntax
Use the pattern `<field>__<operator>=<value>`. Multiple filters combine with
AND by default.
```
GET /api/books?title__ilike=python&publication_date__ge=2020-01-01
```

