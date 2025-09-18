[← Back to Joining Related Resources index](index.md)

# Expected output (example)
With `dump=dynamic` and `join=invoice-lines,payments,customer` you can
expect nested arrays/objects for those relations while other relationships
remain URLs. Example shape:
```
{
  "status_code": 200,
  "total_count": 123,
  "value": [
    {
      "id": 1,
      "number": "INV-0001",
      "date": "2025-09-01",
      "invoice_lines": [
        {"id": 10, "description": "Widget", "quantity": 2, "unit_price": 9.99},
        {"id": 11, "description": "Gadget", "quantity": 1, "unit_price": 19.99}
      ],
      "payments": [
        {"id": 5, "amount": 29.98, "method": "card", "date": "2025-09-05"}
      ],
      "customer": {"id": 7, "name": "Acme Ltd", "email": "billing@acme.test"}
    }
  ]
}
```

