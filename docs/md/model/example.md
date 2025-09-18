[← Back to Config Models index](index.md)

# Example
```
class Author:

    __tablename__ = "author"

    class Meta:
        # adds this model to the "People" tag group in the documentation
        tag_group = "People/Companies"
        # the name of this model in the docs
        group = "Author"
        # a description of this model applied to all endpoints for this model
        description = "Models an author of a book"
        # the rate limit across all HTTP methods for this model
        rate_limit = "10 per minute"  # see RATE_LIMIT <RATE_LIMIT>
```

