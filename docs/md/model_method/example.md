[← Back to Config by Method Models index](index.md)

# Example
```
class Author:
    __tablename__ = "author"
    class Meta:
        # shows this description for the `GET` endpoint in the documentation
        get_description = "Models an author of a book"
        # adds a rate limit of 10 per minute to the `POST` endpoint
        post_rate_limit = "10 per minute"
        # requires authentication for the `GET` endpoint
        get_authenticate = True
        # does not require authentication for the `POST` endpoint
        post_authenticate = False
        # does not require authentication for the `PATCH` endpoint
        patch_authenticate = False
```

