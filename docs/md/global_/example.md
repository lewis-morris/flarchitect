[← Back to Config Globals index](index.md)

# Example
```
class Config:
    # the rate limit across all endpoints in your API
    # If any other, more specific, rate limit is defined, it will
    # override this one for the particular endpoint / method / model.
    API_RATE_LIMIT = "1 per minute"  # see RATE_LIMIT <RATE_LIMIT>
```

