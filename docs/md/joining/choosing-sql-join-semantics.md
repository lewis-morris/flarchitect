[← Back to Joining Related Resources index](index.md)

# Choosing SQL join semantics
Use `join_type` to control the SQL join operator applied to each related
table. Supported values:
- `inner` (default)
- `left` (left outer join)
- `outer` (alias of left for ORM compatibility)
- `right` (best‑effort right join; ORM may emulate using an outer join)
Example:
```

# include base rows even when they have no related books
GET /api/publishers?join=books&join_type=left
```
Invalid values yield `400 Bad Request`.

