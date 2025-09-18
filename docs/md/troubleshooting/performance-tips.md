[← Back to Troubleshooting index](index.md)

# Performance tips
- Prefer `join` with `dump=dynamic` to inline only the relations you need.
- Enable caching for hot GET endpoints and pick a shared backend in prod.
- Use rate limiting for public search routes.

