[← Back to Filtering index](index.md)

# Examples
```

# Books with "python" in the title, published since 2020
GET /api/books?title__ilike=python&publication_date__ge=2020-01-01


# Invoices whose customer name contains "Acme" and total >= 100
GET /api/invoices?join=customer&customer.name__ilike=acme&total__ge=100


# Authors with id 2 OR 3, newest first
GET /api/authors?or[id__eq=2,id__eq=3]&order_by=-id
```

