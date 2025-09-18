[← Back to Getting Started Sample Project index](index.md)

# Run the demo
```
python demo/quickstart/load.py
curl http://localhost:5000/api/authors
```
The curl command answers with a JSON payload that includes some metadata and a `value` list of authors.
Because the demo starts with no records, that list is empty:
```
{
    "total_count": 0,
    "value": []
}
```
Pop open `http://localhost:5000/docs` in your browser to explore the automatically generated API docs.
To optionally restrict access, set the API_DOCUMENTATION_PASSWORD <configuration.html#DOCUMENTATION_PASSWORD> environment variable or enable
API_DOCUMENTATION_REQUIRE_AUTH <configuration.html#DOCUMENTATION_REQUIRE_AUTH>. When protection is active, navigating to `/docs` displays a login
screen that accepts either the configured password or valid user credentials.

