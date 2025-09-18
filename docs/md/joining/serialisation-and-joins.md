[← Back to Joining Related Resources index](index.md)

# Serialisation and joins
Joining models does not by itself inline related objects. See
custom_serialization for how to control nested output. In brief:
- `dump=url` (default) serialises relationships as URLs.
- `dump=json` always nests related objects.
- `dump=dynamic` nests only relationships listed in `join`.
- `dump=hybrid` nests to‑one relationships; collections remain URLs.
Example:
```
GET /api/books?dump=dynamic&join=author,publisher
```

