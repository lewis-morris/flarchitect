[← Back to Advanced Demo index](index.md)

# Run the demo
```
python demo/advanced_features/app.py
curl -X POST http://localhost:5000/api/book \
     -H "Content-Type: application/json" \
     -d '{"title": "my book", "author": {"name": "Alice"}}'
curl http://localhost:5000/api/book?include_deleted=true
```
For authentication strategies and role management, see authentication
and the defining-roles section.

