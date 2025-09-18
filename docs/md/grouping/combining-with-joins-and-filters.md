[← Back to Grouping & Aggregation index](index.md)

# Combining with joins and filters
Grouping and aggregation work with joins, filters, `fields` selection and
ordering:
- Join related tables with `join=` before referencing joined columns in
    `groupby` or aggregate expressions.
- Apply filters (API_ALLOW_FILTERS) to narrow the input rows prior to
    aggregation.
- Use `order_by` to sort by either grouping columns or aggregate labels.

