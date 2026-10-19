[← Back to Extend the generated API index](index.md)

# Choose the smallest extension
- Need different fields, roles, allowed methods or paths? Start with model
    `Meta` configuration.
- Need tenant or owner isolation? Use `API_ACCESS_POLICY.scope_query` and the
    corresponding `can_read`, `can_create`, `can_update` and `can_delete`
    checks. Query hooks are customisation, not a replacement for access policies.
- Need to adjust a query or a record before saving? Use `hook`.
- Need to approve an order or cancel a booking? Use `action`.
- Need a different implementation of one CRUD operation? Use `override`.
- Need a health endpoint or a non-model response? Use `route`.
