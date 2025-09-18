[← Back to Validation index](index.md)

# Basic usage
```
class Author(db.Model):
    email = db.Column(
        db.String,
        info={"validate": "email"},
    )
    website = db.Column(
        db.String,
        info={"format": "uri"},  # auto adds URL validation
    )
```
When invalid data is sent to the API a `400` response is returned:
```
{
  "errors": {"email": ["Email address is not valid."]},
  "status_code": 400,
  "value": null
}
```

