[← Back to Troubleshooting index](index.md)

# Nested objects don’t appear
- Use `dump=dynamic` and list relationships in `join` to inline those only.
- Or set `dump=json` to inline all relationships.
- `API_ADD_RELATIONS` must be enabled and, for deep graphs, consider
    `API_SERIALIZATION_DEPTH` for eager loading.

