[← Back to Custom Serialisation index](index.md)

# Serialisation modes
Set the default with `API_SERIALIZATION_TYPE` (globally or per‑model):
- `url` (default): relationships render as URLs (stable, compact).
- `json`: relationships always render as nested objects.
- `dynamic`: only relationships listed in `join` render as nested objects;
    all others remain URLs.
- `hybrid`: to‑one relationships render as nested objects; collections render
    as URLs.

