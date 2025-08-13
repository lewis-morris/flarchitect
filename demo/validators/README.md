# Validator Demo

This example Flask application showcases how **flarchitect** attaches
field validators to SQLAlchemy models.  The `User` model defines an
`email` field with explicit email validation and a `homepage` field with a
URL validator added via the `format="uri"` hint.

## Running the demo

```bash
python demo/validators/app.py
```

Once running, send a POST request with invalid data to see the validators
in action:

```bash
curl -X POST http://localhost:5000/api/users \
     -H 'Content-Type: application/json' \
     -d '{"email": "not-email", "homepage": "not-url", "slug": "Bad Slug"}'
```

The API responds with `400` and details of the validation failures.
