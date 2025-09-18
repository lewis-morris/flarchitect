[← Back to Validation index](index.md)

# Field validation
`flarchitect` inspects the `info` mapping and the optional `format`
attribute on SQLAlchemy columns to determine which validators to apply.  When
API_AUTO_VALIDATE <configuration.html#AUTO_VALIDATE> is enabled, common formats such as `email` or `date`
are added automatically based on column names.  Any validator supported by
`validate_by_type` can also be assigned manually:
```
class Payment(db.Model):
    account = db.Column(db.String, info={"validate": "iban"})
    cron = db.Column(db.String, info={"format": "cron"})
```
This associates the `iban` and `cron` validators with the `account` and
`cron` columns respectively.  Invalid values cause Marshmallow to raise a
`ValidationError` and the API will respond with `400`.
Multiple validators can be applied to a single column by providing a list:
```
class Contact(db.Model):
    identifier = db.Column(
        db.String,
        info={"validate": ["email", "slug"]},
    )
```
Submitting invalid data returns messages for each failed validator:
```
{
  "errors": {"identifier": ["Email address is not valid.", "Value must be a valid slug."]},
  "status_code": 400,
  "value": null
}
```
Custom error messages can also be supplied via a mapping:
```
class Employee(db.Model):
    email = db.Column(
        db.String,
        info={"validate": {"email": "Invalid email"}},
    )
```
Invalid values return the custom message:
```
{
  "errors": {"email": ["Invalid email"]},
  "status_code": 400,
  "value": null
}
```

