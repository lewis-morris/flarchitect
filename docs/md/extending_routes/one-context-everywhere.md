[← Back to Extend the generated API index](index.md)

# One context everywhere
`OperationContext` is exported from `flarchitect` for type annotations.
It provides `model`, `session`, `operation`, `data` (validated input),
`user` (the current authenticated user, possibly None) and `request`.
Operation names are `list`, `retrieve`, `create`, `update`, `delete`, or
an action's registered name. Context instances belong to one request.
