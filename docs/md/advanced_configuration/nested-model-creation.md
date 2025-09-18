[← Back to Advanced Configuration index](index.md)

# Nested model creation
Nested writes are disabled by default. Enable them globally with
API_ALLOW_NESTED_WRITES <configuration.html#ALLOW_NESTED_WRITES> or per model via
`Meta.allow_nested_writes`.
```
class Config:
    API_ALLOW_NESTED_WRITES = True

class Parent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    children = db.relationship("Child", back_populates="parent")

    class Meta:
        allow_nested_writes = True

class Child(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    parent_id = db.Column(db.Integer, db.ForeignKey("parent.id"))
    parent = db.relationship("Parent", back_populates="children")

    class Meta:
        allow_nested_writes = True
```
With this configuration a nested object can be created in the same request:
```
POST /api/parent
{
    "name": "Jane",
    "children": [{"name": "Junior"}]
}
```

## Depth limits
Once enabled, `AutoSchema` can deserialise nested relationship data during
`POST` or `PUT` requests. Each related model must also opt in with
`Meta.allow_nested_writes` and nesting is capped at **two levels** to avoid
unbounded recursion. Any relationships beyond this depth are ignored.

## Validation errors
Errors raised within nested objects bubble up under their relationship path.
In the following request, the invalid email on the `author` is reported in
the error response:
```
POST /api/book
{
    "title": "My Book",
    "author": {"email": "not-an-email"}
}

{
    "errors": {"author": {"email": ["Not a valid email address."]}}
}
```

## Example: multiple nested levels
With nested writes enabled you can create several related objects at once,
up to two levels deep:
```
{
    "title": "My Book",
    "isbn": "12345",
    "publication_date": "2024-01-01",
    "author": {
        "first_name": "John",
        "last_name": "Doe",
        "publisher": {
            "name": "Acme Publishing"
        }
    }
}
```
To partially update a nested relationship, send only the fields you want to
change in a `PATCH` request:
```
PATCH /books/1
{
    "author": {
        "id": 1,
        "biography": "Updated bio"
    }
}
```
The nested `author` object is deserialised into an `Author` instance while
responses continue to use the configured serialisation type (URL, JSON, or
dynamic).

