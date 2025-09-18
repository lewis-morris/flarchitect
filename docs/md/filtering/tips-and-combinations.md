[← Back to Filtering index](index.md)

# Tips and combinations
- Filters compose with other query features like joining <joining>,
    sorting (`order_by`), pagination (`page`/`limit`), and dynamic nesting
    via custom_serialization (e.g. `dump=dynamic`).
- For list comparisons (`in`/`nin`) pass values in parentheses, comma‑separated
    as shown above.
- When joining one‑to‑many relationships, pagination operates over distinct base
    rows; see joining for details on join semantics.

