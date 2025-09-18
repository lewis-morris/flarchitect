[← Back to Troubleshooting index](index.md)

# Pagination counts look wrong with joins
- flarchitect applies `DISTINCT` on base rows for typical join queries so
    `limit`/`total_count` operate over base entities instead of multiplied
    join rows. If you use custom `fields`/`groupby`/aggregations, ensure your
    projection reflects the desired counting semantics.

