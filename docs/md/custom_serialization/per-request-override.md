[← Back to Custom Serialisation index](index.md)

# Per‑request override
Clients can override the mode with a `dump` query parameter. Invalid values
are ignored and the configured default is used.
Examples:
```

# dynamic serialisation for this request only
GET /api/invoices?dump=dynamic&join=invoice-lines,payments,customer


# always nest all relations
GET /api/books?dump=json
```

