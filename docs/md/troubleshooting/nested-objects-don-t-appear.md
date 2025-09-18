[← Back to Troubleshooting index](index.md)

# Nested objects don’t appear
- Use `dump=dynamic` and list relationships in `join` to inline those only.
> - With `API_ADD_RELATIONS=False`, relationships are omitted by default. You
>     can still inline specific ones by combining `dump=dynamic` with
>     `join=...` or by selecting joined fields (e.g., `fields=title,author.first_name`),
>     which preserves those fields in the response.
- Or set `dump=json` to inline all relationships.
- `API_ADD_RELATIONS` must be enabled and, for deep graphs, consider
    `API_SERIALIZATION_DEPTH` for eager loading.

