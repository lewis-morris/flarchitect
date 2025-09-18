[← Back to Extensions index](index.md)

# Extending query parameters
Use ADDITIONAL_QUERY_PARAMS <configuration.html#ADDITIONAL_QUERY_PARAMS> to document extra query parameters introduced in
a return callback. The value is a list of OpenAPI parameter objects.
```
class Config:
    API_ADDITIONAL_QUERY_PARAMS = [{
        "name": "log",
        "in": "query",
        "description": "Log call into the database",
        "schema": {"type": "string"},
    }]

class Author(db.Model):
    class Meta:
        get_additional_query_params = [{
            "name": "log",
            "in": "query",
            "schema": {"type": "string"},
        }]
```

