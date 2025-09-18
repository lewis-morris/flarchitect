[← Back to Advanced Demo index](index.md)

# Key points
- **Soft deletes** are enabled via API_SOFT_DELETE <configuration.html#SOFT_DELETE> and the `deleted` column on `BaseModel` (see soft-delete).
- **Nested writes** allow creating related objects in one request. `Book.Meta.allow_nested_writes` turns it on for books.
- **Custom callbacks** modify behaviour: `return_callback` injects a `debug` flag into every response and `Book.Meta.add_callback` title-cases book names before saving.

