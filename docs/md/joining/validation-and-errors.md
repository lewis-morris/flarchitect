[← Back to Joining Related Resources index](index.md)

# Validation and errors
Join support is opt‑in. If `API_ALLOW_JOIN` is disabled (globally or for the
model), `join` is ignored. When joins are enabled, every token must resolve to
an actual relationship from the base model. Unknown tokens result in
`400 Bad Request` with a message of the form:
```
{"errors": {"error": "Invalid join model: <token>"}, "status_code": 400}
```
Guidelines:
- Provide a comma‑separated list in a single `join` parameter, e.g.:
    ```
    GET /api/invoices?join=invoice-lines,payments,customer
    ```
- Ensure each relationship exists on the base model. For example, if
    `invoice_lines` is not a relationship on `Invoice`, the request fails with
    `Invalid join model: invoice-lines`.
> **Tip**
> Use custom_serialization (`dump=dynamic` or `dump=json`) together
> with `API_ADD_RELATIONS=True` to inline joined objects into the response.

