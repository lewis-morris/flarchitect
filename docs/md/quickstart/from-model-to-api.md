[← Back to Quick Start index](index.md)

# From Model to API
Turn this:
```
class Book(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    author = db.Column(db.String(80), nullable=False)
    published = db.Column(db.DateTime, nullable=False)
```
Into this:
`GET /api/books`
```
{
  "datetime": "2024-01-01T00:00:00.0000+00:00",
  "api_version": "0.1.0",
  "status_code": 200,
  "response_ms": 15,
  "total_count": 10,
  "next_url": "/api/authors?limit=2&page=3",
  "previous_url": "/api/authors?limit=2&page=1",
  "errors": null,
  "value": [
    {
      "author": "John Doe",
      "id": 3,
      "published": "2024-01-01T00:00:00.0000+00:00",
      "title": "The Book"
    },
    {
      "author": "Jane Doe",
      "id": 4,
      "published": "2024-01-01T00:00:00.0000+00:00",
      "title": "The Book 2"
    }
  ]
}
```

