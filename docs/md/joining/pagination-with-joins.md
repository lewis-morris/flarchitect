[← Back to Joining Related Resources index](index.md)

# Pagination with joins
Joining one‑to‑many relationships multiplies result rows at the SQL level. To
keep pagination intuitive, flarchitect applies `DISTINCT` to the base entity
whenever you request joins without a custom `fields`/`groupby`/aggregation
projection. This ensures that `limit` and `total_count` operate over
distinct base rows rather than multiplied join rows.

