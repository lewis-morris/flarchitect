[← Back to Filtering index](index.md)

# OR conditions
To express OR logic, wrap a comma‑separated list of full conditions inside a
single `or[ ... ]` parameter. The contained conditions are grouped with one
`OR` clause and combined with any other filters using `AND`.
```

# Authors with id 2 OR 3
GET /api/authors?or[id__eq=2,id__eq=3]
```

